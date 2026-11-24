import re
import unicodedata
import pandas as pd
import requests

ANOS = (2020, 2021, 2025)
COMPETICOES = {
    "Copa do Brasil": "brasil-copa-do-brasil",
    "Libertadores": "america-copa-libertadores",
}

# Resultados historicos para distinguir campeao e vice entre os finalistas
# efetivamente encontrados nas partidas. Nao sao usados para inventar campanhas.
FINAIS = {
    ("Copa do Brasil", 2020): ("Palmeiras", "Grêmio"),
    ("Copa do Brasil", 2021): ("Atlético-MG", "Athletico-PR"),
    ("Copa do Brasil", 2025): ("Corinthians", "Vasco"),
    ("Libertadores", 2020): ("Palmeiras", "Santos"),
    ("Libertadores", 2021): ("Palmeiras", "Flamengo"),
    ("Libertadores", 2025): ("Flamengo", "Palmeiras"),
}

# Apelidos exclusivos para conferir os finalistas (nao alteram nomes da fonte).
ALIAS = {
    "Palmeiras": ("palmeiras",),
    "Grêmio": ("gremio",),
    "Atlético-MG": ("atletico mineiro", "atletico mg", "atl mineiro"),
    "Athletico-PR": (
        "athletico paranaense", "atletico paranaense",
        "athletico pr", "atletico pr", "athletico", "paranaense",
    ),
    "Corinthians": ("corinthians",),
    "Vasco": ("vasco",),
    "Santos": ("santos",),
    "Flamengo": ("flamengo",),
}

COLUNAS_SAIDA = [
    "clube", "ano", "competicao", "fase_alcancada", "fonte", "clube_origem"
]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto.lower()).split())


def identificar_nome(nome_fonte, nome_referencia):
    texto = normalizar(nome_fonte)
    return any(
        re.search(r"(?:^| )" + re.escape(alias) + r"(?: |$)", texto)
        for alias in ALIAS[nome_referencia]
    )


def extrair_partidas():
    partes = []
    with requests.Session() as sessao:
        for competicao, identificador in COMPETICOES.items():
            for ano in ANOS:
                url = (
                    "https://raw.githubusercontent.com/FerrerasRP/FootballData/"
                    f"main/database/{identificador}/{identificador} {ano}.json"
                )
                try:
                    resposta = sessao.get(url, timeout=45)
                    resposta.raise_for_status()
                    dados = resposta.json()
                except (requests.RequestException, ValueError) as erro:
                    raise RuntimeError(
                        f"Falha ao obter {competicao} {ano} em {url}: {erro}"
                    ) from erro

                if not isinstance(dados, list) or not dados:
                    raise ValueError(f"JSON vazio ou inesperado: {competicao} {ano}")

                df = pd.DataFrame(dados)
                obrigatorias = ["match_date", "round", "home", "away"]
                ausentes = [col for col in obrigatorias if col not in df.columns]
                if ausentes:
                    raise ValueError(f"{competicao} {ano}: colunas ausentes: {ausentes}")
                if df[obrigatorias].isna().any().any():
                    raise ValueError(f"{competicao} {ano}: campos obrigatorios nulos")

                for coluna in ("round", "home", "away"):
                    df[coluna] = df[coluna].astype(str).str.strip()
                    if df[coluna].eq("").any():
                        raise ValueError(f"{competicao} {ano}: campo {coluna} vazio")

                df["ano"] = ano  # ano da edicao, nao necessariamente do calendario
                df["competicao"] = competicao
                df["fonte"] = "GitHub - FerrerasRP"
                partes.append(df)
                print(f"{competicao} {ano}: {len(df)} partidas extraidas")

    df = pd.concat(partes, ignore_index=True)
    df["data"] = pd.to_datetime(
        df["match_date"].astype(str).str.slice(0, 10),
        format="%d.%m.%Y",
        errors="raise",
    )
    return df


def separar_pre_libertadores(df_partidas):
    df = df_partidas.copy()
    rodadas = df["round"].str.upper().str.strip()
    eh_lib = df["competicao"].eq("Libertadores")
    eh_grupo = rodadas.str.match(r"^RODADA\s+\d+$", na=False)

    inicio_grupos = df.loc[eh_lib & eh_grupo].groupby("ano")["data"].min()
    if set(inicio_grupos.index) != set(ANOS):
        raise ValueError(
            "Nao foi possivel identificar o inicio da fase de grupos da "
            f"Libertadores em todos os anos: {inicio_grupos.to_dict()}"
        )

    df["fase"] = "Principal"
    limite = df["ano"].map(inicio_grupos)
    eh_pre = eh_lib & ~eh_grupo & df["data"].lt(limite)
    df.loc[eh_pre, "fase"] = "Classificatória"

    # Esta verificacao evita confundir uma FINAL preliminar com a decisao real.
    for ano in ANOS:
        finais_principais = df.loc[
            eh_lib & df["ano"].eq(ano) & rodadas.eq("FINAL")
            & df["fase"].eq("Principal")
        ]
        if len(finais_principais) != 1:
            raise ValueError(
                f"Libertadores {ano}: esperada exatamente uma partida "
                f"da final principal, encontradas {len(finais_principais)}"
            )

    return df


def classificar_fase(ano, competicao, rodada, etapa):
    nome = str(rodada).strip().upper()

    if competicao == "Libertadores":
        if etapa == "Classificatória":
            return {
                "QUARTAS DE FINAL": (1, "Pré-Libertadores - Fase 1"),
                "SEMIFINAIS": (2, "Pré-Libertadores - Fase 2"),
                "FINAL": (3, "Pré-Libertadores - Fase 3"),
            }.get(nome, (-1, "VERIFICAR"))
        if re.fullmatch(r"RODADA\s+\d+", nome):
            return 10, "Fase de grupos"

    elif competicao == "Copa do Brasil":
        iniciais = (
            {
                "128 AVOS DE FINAL": (10, "Primeira fase"),
                "64 AVOS DE FINAL": (20, "Segunda fase"),
                "32 AVOS DE FINAL": (30, "Terceira fase"),
                "16 AVOS DE FINAL": (40, "Quarta fase"),
            }
            if ano == 2020 else
            {
                "64 AVOS DE FINAL": (10, "Primeira fase"),
                "32 AVOS DE FINAL": (20, "Segunda fase"),
                "16 AVOS DE FINAL": (30, "Terceira fase"),
            }
        )
        if nome in iniciais:
            return iniciais[nome]
    else:
        return -1, "VERIFICAR"

    return {
        "OITAVAS DE FINAL": (50, "Oitavas de final"),
        "QUARTAS DE FINAL": (60, "Quartas de final"),
        "SEMIFINAIS": (70, "Semifinal"),
        "FINAL": (80, "Finalista"),
    }.get(nome, (-1, "VERIFICAR"))


def consolidar_clubes(df_partidas):
    df = df_partidas.copy()
    classificacoes = df.apply(
        lambda x: classificar_fase(
            int(x["ano"]), x["competicao"], x["round"], x["fase"]
        ), axis=1,
    )
    df["ordem"] = classificacoes.map(lambda x: x[0])
    df["fase_alcancada"] = classificacoes.map(lambda x: x[1])

    erros = df.loc[df["ordem"].eq(-1), ["ano", "competicao", "round", "fase"]]
    if not erros.empty:
        print("Fases nao reconhecidas:\n", erros.drop_duplicates().to_string(index=False))
        raise ValueError("Existem fases nao reconhecidas nos JSONs")

    colunas = ["ano", "competicao", "fase_alcancada", "ordem", "fonte"]
    mandantes = df[colunas + ["home"]].rename(columns={"home": "clube"})
    visitantes = df[colunas + ["away"]].rename(columns={"away": "clube"})
    clubes = pd.concat([mandantes, visitantes], ignore_index=True)

    # Melhor fase em que cada clube aparece, sem tentar inferir placar agregado.
    clubes = (
        clubes.sort_values("ordem", kind="stable")
        .drop_duplicates(["ano", "competicao", "clube"], keep="last")
    )

    brasileiros_lib = clubes["clube"].str.contains(
        r"\(Bra\)\s*$", case=False, na=False, regex=True
    )
    filtro = clubes["competicao"].eq("Copa do Brasil") | (
        clubes["competicao"].eq("Libertadores") & brasileiros_lib
    )
    clubes = clubes.loc[filtro].copy()
    clubes["clube_origem"] = clubes["clube"]
    clubes["clube"] = (
        clubes["clube"]
        .str.replace(r"\s*\(Bra\)\s*$", "", regex=True, case=False)
        .str.strip()
    )
    clubes = clubes.drop(columns=["ordem"]).reset_index(drop=True)
    return clubes


def verificar_finalistas(df_clubes):
    df = df_clubes.copy()
    for (competicao, ano), (campeao, vice) in FINAIS.items():
        filtro = (
            df["ano"].eq(ano)
            & df["competicao"].eq(competicao)
            & df["fase_alcancada"].eq("Finalista")
        )
        finalistas = df.loc[filtro]
        if len(finalistas) != 2:
            print("Finalistas encontrados:\n", finalistas.to_string(index=False))
            raise ValueError(
                f"{competicao} {ano}: esperados 2 finalistas, "
                f"encontrados {len(finalistas)}"
            )

        encontrados_campeao = [
            i for i in finalistas.index
            if identificar_nome(df.at[i, "clube"], campeao)
        ]
        encontrados_vice = [
            i for i in finalistas.index
            if identificar_nome(df.at[i, "clube"], vice)
        ]
        if (
            len(encontrados_campeao) != 1
            or len(encontrados_vice) != 1
            or encontrados_campeao[0] == encontrados_vice[0]
        ):
            raise ValueError(
                f"Nao foi possivel reconhecer os finalistas de "
                f"{competicao} {ano}: {finalistas['clube'].tolist()}"
            )
        df.at[encontrados_campeao[0], "fase_alcancada"] = "Campeão"
        df.at[encontrados_vice[0], "fase_alcancada"] = "Vice-campeão"

    duplicados = df.duplicated(["ano", "competicao", "clube"])
    if duplicados.any():
        print("Duplicados:\n", df.loc[duplicados].to_string(index=False))
        raise ValueError("Registros duplicados apos o tratamento")

    for ano in ANOS:
        for competicao in COMPETICOES:
            parte = df.loc[df["ano"].eq(ano) & df["competicao"].eq(competicao)]
            if parte.empty:
                raise ValueError(f"Sem registros de {competicao} {ano}")
            if (
                parte["fase_alcancada"].eq("Campeão").sum() != 1
                or parte["fase_alcancada"].eq("Vice-campeão").sum() != 1
                or parte["fase_alcancada"].eq("Finalista").any()
            ):
                raise ValueError(f"Classificacao da final inconsistente: {competicao} {ano}")

    return df.sort_values(["ano", "competicao", "clube"]).reset_index(drop=True)

# EXECUCAO E ARMAZENAMENTO

# A sessao 'spark' ja deve existir no Databricks.
if "spark" not in globals():
    raise RuntimeError("Execute este script em um notebook com sessao Spark ativa.")

# Toda a extracao e validacao acontece ANTES de sobrescrever as tabelas.
df_json_historico = extrair_partidas()
df_json_historico = separar_pre_libertadores(df_json_historico)
df_copas_brasileiros = consolidar_clubes(df_json_historico)
df_copas_brasileiros = verificar_finalistas(df_copas_brasileiros)

df_copa_final = df_copas_brasileiros.loc[
    df_copas_brasileiros["competicao"].eq("Copa do Brasil"), COLUNAS_SAIDA
].copy()
df_lib_final = df_copas_brasileiros.loc[
    df_copas_brasileiros["competicao"].eq("Libertadores"), COLUNAS_SAIDA
].copy()

for nome, frame in (("Copa do Brasil", df_copa_final), ("Libertadores", df_lib_final)):
    if frame.empty:
        raise ValueError(f"Nenhum dado para gravar: {nome}")
    if frame[COLUNAS_SAIDA].isna().any().any():
        raise ValueError(f"Valores nulos antes da gravação: {nome}")
    frame["ano"] = frame["ano"].astype("int32")

print("\nRegistros por temporada e competicao:")
print(df_copas_brasileiros.groupby(["ano", "competicao"]).size().to_string())
print("\nCampeoes e vice-campeoes:")
print(
    df_copas_brasileiros.loc[
        df_copas_brasileiros["fase_alcancada"].isin(["Campeão", "Vice-campeão"]),
        ["ano", "competicao", "clube", "fase_alcancada"],
    ].to_string(index=False)
)

# Grava as duas tabelas intermediarias Delta no schema corrente.
spark.createDataFrame(df_copa_final).write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("stg_copa_do_brasil_historico_extra")

print("Tabela stg_copa_do_brasil_historico_extra criada com sucesso!")

spark.createDataFrame(df_lib_final).write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("stg_libertadores_historico_extra")

print("Tabela stg_libertadores_historico_extra criada com sucesso!")