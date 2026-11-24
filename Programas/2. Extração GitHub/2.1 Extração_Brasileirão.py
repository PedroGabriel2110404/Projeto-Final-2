import pandas as pd
from pyspark.sql import functions as F

# 1. CONFIGURAÇÃO
anos = [2020, 2021, 2025]
tabelas = []

# 2. EXTRAÇÃO DOS ARQUIVOS CSV
for ano in anos:

    url = (
        "https://raw.githubusercontent.com/"
        "guisomera/brasileirao-position-predictor/"
        f"main/br_{ano}_38.csv"
    )

    df = pd.read_csv(url)

    # Verificar as colunas necessárias
    colunas_esperadas = [
        "Posição", "Clube", "Vitorias", "Empates",
        "Derrotas", "Gols feitos", "Gols sofridos",
        "Pontos"
    ]

    faltantes = [
        coluna for coluna in colunas_esperadas
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"{ano}: colunas ausentes: {faltantes}"
        )

    # Padronizar nomes das colunas
    df = df.rename(columns={
        "Posição": "posicao_final",
        "Clube": "clube",
        "Vitorias": "vitorias",
        "Empates": "empates",
        "Derrotas": "derrotas",
        "Gols feitos": "gols_pro",
        "Gols sofridos": "gols_contra",
        "Pontos": "pontos"
    })

    # Converter campos numéricos
    colunas_numericas = [
        "posicao_final", "pontos",
        "vitorias", "empates", "derrotas"
    ]

    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(
            df[coluna], errors="raise"
        )

        if df[coluna].isna().any():
            raise ValueError(
                f"{ano}: valores nulos em {coluna}."
            )

        df[coluna] = df[coluna].astype(int)

# 3. VALIDAÇÃO DOS DADOS

    # Conferir quantidade de clubes
    if len(df) != 20:
        raise ValueError(
            f"{ano}: esperados 20 clubes, "
            f"encontrados {len(df)}."
        )

    # Verificar nomes
    if df["clube"].isna().any():
        raise ValueError(
            f"{ano}: existem clubes sem nome."
        )

    df["clube"] = df["clube"].str.strip()

    if df["clube"].eq("").any():
        raise ValueError(
            f"{ano}: existem nomes de clubes vazios."
        )

    # Verificar clubes duplicados
    if df["clube"].duplicated().any():
        raise ValueError(
            f"{ano}: clubes duplicados."
        )

    # Verificar posições de 1 a 20
    if sorted(df["posicao_final"].tolist()) != list(range(1, 21)):
        raise ValueError(
            f"{ano}: posições finais inconsistentes."
        )

    # Verificar total de partidas
    jogos = (
        df["vitorias"]
        + df["empates"]
        + df["derrotas"]
    )

    if (jogos != 38).any():
        raise ValueError(
            f"{ano}: clubes com quantidade "
            "incorreta de jogos."
        )

    # Verificar pontuação
    pontos_calculados = (
        3 * df["vitorias"]
        + df["empates"]
    )

    if (df["pontos"] != pontos_calculados).any():
        raise ValueError(
            f"{ano}: pontuações inconsistentes."
        )

# 4. PADRONIZAÇÃO PARA O BANCO

    df["ano"] = ano
    df["competicao"] = "Brasileirão"

    # Manter apenas os campos utilizados na integração
    df = df[
        [
            "clube",
            "ano",
            "competicao",
            "posicao_final",
            "pontos",
        ]
    ].copy()

    tabelas.append(df)

    print(f"{ano}: {len(df)} clubes extraídos e validados")

# 5. CONSOLIDAÇÃO E VALIDAÇÃO FINAL
df_br_faltantes = pd.concat(
    tabelas,
    ignore_index=True
)

# Conferir quantidade total
total_esperado = len(anos) * 20

if len(df_br_faltantes) != total_esperado:
    raise ValueError(
        f"Esperados {total_esperado} registros, "
        f"encontrados {len(df_br_faltantes)}."
    )

# Verificar duplicações entre clubes e temporadas
duplicados = df_br_faltantes.duplicated(
    subset=["ano", "clube"]
)

if duplicados.any():
    raise ValueError(
        f"Foram encontrados {duplicados.sum()} "
        "registros duplicados."
    )

df_br_faltantes = df_br_faltantes.sort_values(
    ["ano", "posicao_final"]
).reset_index(drop=True)

print("\nExtração e validação concluídas!")
print(f"Total de registros: {len(df_br_faltantes)}")

display(df_br_faltantes)

# 6. ARMAZENAMENTO NO DATABRICKS

df_spark_br = spark.createDataFrame(
    df_br_faltantes
)

df_spark_br = df_spark_br.withColumn(
    "fase_alcancada",
    F.lit(None).cast("string")
)

df_spark_br.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("stg_brasileirao_historico_extra")

print(
    "\nTabela stg_brasileirao_historico_extra "
    "criada com sucesso!"
)