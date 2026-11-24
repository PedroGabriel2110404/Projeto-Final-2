import pandas as pd
import requests

# 1. CONFIGURAÇÃO DA API
API_KEY = "SUA_CHAVE_API" #insira a sua API aqui
url = "https://v3.football.api-sports.io/standings"
ID_LIGA = 71
anos = (2022, 2023, 2024)
registros = []

# 2. EXTRAÇÃO DOS DADOS
for ano in anos:

    response = requests.get(
        url,
        headers=headers,
        params={
            "league": ID_LIGA,
            "season": ano
        },
        timeout=30
    )

    # Lê a resposta antes de verificar erros HTTP
    try:
        dados = response.json()
    except ValueError:
        raise RuntimeError(
            f"{ano}: resposta inválida da API. "
            f"HTTP {response.status_code}"
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"{ano}: erro HTTP {response.status_code}. "
            f"Detalhes: {dados.get('errors', dados)}"
        )

    if dados.get("errors") or not dados.get("response"):
        raise RuntimeError(
            f"{ano}: falha na extração. "
            f"Detalhes: {dados.get('errors')}"
        )

    classificacao = dados["response"][0]["league"]["standings"][0]

    # Organiza os dados extraídos
    for time in classificacao:
        registros.append({
            "id_api_clube": time["team"]["id"],
            "clube": time["team"]["name"],
            "ano": ano,
            "posicao_final": time["rank"],
            "pontos": time["points"],
        })

    print(f"{ano}: {len(classificacao)} clubes extraídos")

# 3. VALIDAÇÃO DOS DADOS
df_brasileirao = pd.DataFrame(registros)

# Verifica duplicidades por clube e temporada
duplicados = df_brasileirao.duplicated(
    subset=["id_api_clube", "ano"]
)

if duplicados.any():
    raise ValueError(
        f"Foram encontrados {duplicados.sum()} "
        "registros duplicados."
    )

# Verifica se todas as temporadas foram extraídas
total_esperado = len(anos) * 20

if len(df_brasileirao) != total_esperado:
    raise ValueError(
        f"Esperados {total_esperado} registros, "
        f"mas foram encontrados {len(df_brasileirao)}."
    )

# Verifica se os campos principais estão preenchidos
campos_obrigatorios = [
    "id_api_clube",
    "clube",
    "ano",
    "posicao_final",
    "pontos"
]

if df_brasileirao[campos_obrigatorios].isnull().any().any():
    raise ValueError(
        "Existem valores nulos nos campos obrigatórios."
    )

# Ordena por temporada e posição final
df_brasileirao = df_brasileirao.sort_values(
    ["ano", "posicao_final"]
).reset_index(drop=True)

print("\nValidação concluída com sucesso!")
print(f"Total de registros: {len(df_brasileirao)}")

display(df_brasileirao)

# 4. ARMAZENAMENTO NO DATABRICKS

# Converte Pandas para Spark
df_spark_bras = spark.createDataFrame(df_brasileirao)

# Salva como tabela Delta
df_spark_bras.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("resultados_brasileirao")

print("\nTabela resultados_brasileirao criada com sucesso!")