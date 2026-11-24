import requests
import pandas as pd
import re
import unicodedata

API_KEY = "SUA_CHAVE_API" #Insira a chave da API aqui

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY.strip()
}

ANOS = (2022, 2023, 2024)

COMPETICOES = {
    "Copa do Brasil": 73,
    "Libertadores": 13
}
# Campeoes oficiais: nao inferir o titulo a partir do vencedor de um jogo.
CAMPEOES = {
    ("Copa do Brasil", 2022): "Flamengo",
    ("Copa do Brasil", 2023): "Sao Paulo",
    ("Copa do Brasil", 2024): "Flamengo",
    ("Libertadores", 2022): "Flamengo",
    ("Libertadores", 2023): "Fluminense",
    ("Libertadores", 2024): "Botafogo",
}

def consultar(endpoint, params):
    resposta = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=60,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    if dados.get("errors"):
        raise RuntimeError(f"API retornou erro em {endpoint} {params}: {dados['errors']}")
    if dados.get("paging", {}).get("total", 1) > 1:
        raise RuntimeError(f"Resposta paginada em {endpoint} {params}; revisar extracao.")
    registros = dados.get("response", [])
    if not registros:
        raise RuntimeError(f"Resposta vazia em {endpoint} {params}.")
    return registros


def normalizar(texto):
    sem_acentos = unicodedata.normalize("NFKD", str(texto))
    sem_acentos = "".join(c for c in sem_acentos if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-zA-Z0-9]+", " ", sem_acentos).lower().split())


def identificar_fase(rotulo, competicao):
    """Retorna (ordem, fase) ou (None, None) para rotulo desconhecido."""
    texto = normalizar(rotulo)

    if "semi final" in texto or "semifinal" in texto:
        return 80, "Semifinal"
    if "quarter final" in texto or "quartas" in texto or "1 4 final" in texto:
        return 70, "Quartas de final"
    if "round of 16" in texto or "oitavas" in texto or "8th final" in texto or "1 8 final" in texto:
        return 60, "Oitavas de final"
    if "round of 32" in texto or "16th final" in texto or "1 16 final" in texto:
        return 50, "16 avos de final"
    if "final" in texto:
        return 100, "Finalista"
    if "group" in texto or "grupo" in texto:
        return 40, "Fase de grupos"

    equivalencias = {"first": 1, "second": 2, "third": 3, "fourth": 4}
    numero = None
    match = re.search(r"\b([1-4])(?:st|nd|rd|th)?\s+(?:(?:qualifying|preliminary)\s+)?(?:round|phase|stage|fase)\b", texto)
    if match:
        numero = int(match.group(1))
    else:
        match = re.search(r"\b(?:round|phase|stage|fase)\s+([1-4])\b", texto)
        if match:
            numero = int(match.group(1))
        else:
            for palavra, n in equivalencias.items():
                if re.search(rf"\b{palavra}\s+(?:round|phase|stage|fase)\b", texto):
                    numero = n
                    break

    if numero is not None:
        if competicao == "Libertadores":
            # Na Libertadores, rodadas numeradas ANTES dos grupos sao qualificatorias.
            return numero * 10, f"Pré-Libertadores - fase {numero}"
        nomes = {1: "Primeira fase", 2: "Segunda fase", 3: "Terceira fase", 4: "Quarta fase"}
        return numero * 10, nomes[numero]
    return None, None


def extrair():
    # Restricao da amostra: clubes da Serie A na propria temporada.
    ids_serie_a = {}
    for ano in ANOS:
        resposta = consultar("standings", {"league": 71, "season": ano})
        tabela = resposta[0]["league"]["standings"][0]
        ids = {linha["team"]["id"] for linha in tabela}
        if len(tabela) != 20 or len(ids) != 20:
            raise ValueError(f"Serie A {ano}: esperados 20 clubes distintos; retornaram {len(ids)}.")
        ids_serie_a[ano] = ids
        print(f"Serie A {ano}: 20 clubes identificados")

    melhores = {}
    fases_desconhecidas = set()

    for ano in ANOS:
        for competicao, liga in COMPETICOES.items():
            partidas = consultar("fixtures", {"league": liga, "season": ano})
            print(f"{competicao} {ano}: {len(partidas)} partidas retornadas")
            for jogo in partidas:
                if jogo["fixture"]["status"]["short"] not in ("FT", "AET", "PEN"):
                    continue
                rotulo = jogo["league"].get("round") or ""
                ordem, fase = identificar_fase(rotulo, competicao)
                for lado in ("home", "away"):
                    clube = jogo["teams"][lado]
                    id_clube = clube.get("id")
                    if id_clube not in ids_serie_a[ano]:
                        continue
                    if ordem is None:
                        fases_desconhecidas.add((competicao, ano, rotulo))
                        continue
                    chave = (competicao, ano, id_clube)
                    if chave not in melhores or ordem > melhores[chave]["ordem"]:
                        melhores[chave] = {
                            "id_api_clube": id_clube,
                            "clube": clube["name"],
                            "ano": ano,
                            "competicao": competicao,
                            "fase_alcancada": fase,
                            "fase_original": rotulo,
                            "ordem": ordem,
                        }

    if fases_desconhecidas:
        detalhes = "\n".join(str(x) for x in sorted(fases_desconhecidas))
        raise ValueError(f"Fases nao reconhecidas; revisar nomes reais da API:\n{detalhes}")

    # Uma final pode conter apenas um clube brasileiro na amostra.
    for (competicao, ano), campeao_nome in CAMPEOES.items():
        finalistas = [
            linha for linha in melhores.values()
            if linha["competicao"] == competicao
            and linha["ano"] == ano
            and linha["fase_alcancada"] == "Finalista"
        ]
        campeoes_encontrados = [
            linha for linha in finalistas
            if normalizar(linha["clube"]) == normalizar(campeao_nome)
        ]
        if len(campeoes_encontrados) != 1:
            raise ValueError(
                f"Campeao {campeao_nome} nao aparece como finalista em "
                f"{competicao} {ano}. Finalistas da amostra: "
                f"{[linha['clube'] for linha in finalistas]}"
            )
        for linha in finalistas:
            linha["fase_alcancada"] = (
                "Campeão" if linha is campeoes_encontrados[0] else "Vice-campeão"
            )
            if linha is campeoes_encontrados[0]:
                linha["ordem"] = 110

    df = pd.DataFrame(melhores.values())
    if df.empty:
        raise RuntimeError("Nao foram produzidos registros.")
    if df.duplicated(subset=["id_api_clube", "ano", "competicao"]).any():
        raise RuntimeError("Registros duplicados detectados.")
    for ano in ANOS:
        for competicao in COMPETICOES:
            if not ((df["ano"] == ano) & (df["competicao"] == competicao)).any():
                raise RuntimeError(f"Nenhum clube da Serie A em {competicao} {ano}.")

    return df.sort_values(["ano", "competicao", "ordem", "clube"],
                          ascending=[True, True, False, True]).reset_index(drop=True)


df_copas = extrair()
print("\nResumo dos registros:")
print(df_copas.groupby(["ano", "competicao"]).size().to_string())