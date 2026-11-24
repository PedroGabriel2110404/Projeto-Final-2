from pyspark.sql import functions as F

# 1. CARREGAR AS TABELAS HISTÓRICAS
df_br = spark.table(
    "stg_brasileirao_historico_extra"
)

df_copa = spark.table(
    "stg_copa_do_brasil_historico_extra"
)

df_lib = spark.table(
    "stg_libertadores_historico_extra"
)

# 2. PADRONIZAR AS COLUNAS
def padronizar(df, fonte_padrao):

    def campo(nome, tipo):
        if nome in df.columns:
            return F.col(nome).cast(tipo).alias(nome)

        return F.lit(None).cast(tipo).alias(nome)

    return df.select(
        campo("clube", "string"),
        campo("ano", "int"),
        campo("competicao", "string"),
        campo("posicao_final", "int"),
        campo("pontos", "int"),
        campo("fase_alcancada", "string"),
        (
            F.col("fonte").cast("string")
            if "fonte" in df.columns
            else F.lit(fonte_padrao)
        ).alias("fonte")
    )


br = padronizar(df_br, "GitHub - guisomera")
copa = padronizar(df_copa, "GitHub - FerrerasRP")
lib = padronizar(df_lib, "GitHub - FerrerasRP")

# 3. CONSOLIDAR OS RESULTADOS
df_historico_extra = (
    br.unionByName(copa)
      .unionByName(lib)
)

print("RESULTADOS HISTÓRICOS CONSOLIDADOS:")

display(
    df_historico_extra.orderBy(
        "ano", "competicao", "clube"
    )
)

# 4. VALIDAR OS RESULTADOS

# Contar registros por ano e competição
resumo = (
    df_historico_extra
    .groupBy("ano", "competicao")
    .count()
    .orderBy("ano", "competicao")
)

print("REGISTROS POR ANO E COMPETIÇÃO:")
display(resumo)

# Verificar duplicações
duplicados = (
    df_historico_extra
    .groupBy("clube", "ano", "competicao")
    .count()
    .filter(F.col("count") > 1)
)

quantidade_duplicados = duplicados.count()

# Verificar campos obrigatórios
nulos = df_historico_extra.filter(
    F.col("clube").isNull()
    | F.col("ano").isNull()
    | F.col("competicao").isNull()
)

quantidade_nulos = nulos.count()

# Verificar as nove combinações esperadas
anos = [2020, 2021, 2025]

competicoes = [
    "Brasileirão",
    "Copa do Brasil",
    "Libertadores"
]

combinacoes_esperadas = {
    (ano, competicao)
    for ano in anos
    for competicao in competicoes
}

combinacoes_encontradas = {
    (linha["ano"], linha["competicao"])
    for linha in resumo.collect()
}

# Verificar quantidade de clubes no Brasileirão
quantidade_brasileirao = (
    df_historico_extra
    .filter(F.col("competicao") == "Brasileirão")
    .count()
)

print("\nRESUMO DA VALIDAÇÃO:")
print("Registros:", df_historico_extra.count())
print("Duplicados:", quantidade_duplicados)
print("Campos obrigatórios nulos:", quantidade_nulos)
print("Combinações:", len(combinacoes_encontradas))
print("Registros do Brasileirão:", quantidade_brasileirao)

if quantidade_duplicados > 0:
    display(duplicados)
    raise ValueError("Existem registros duplicados.")

if quantidade_nulos > 0:
    display(nulos)
    raise ValueError("Existem campos obrigatórios nulos.")

if combinacoes_encontradas != combinacoes_esperadas:
    raise ValueError(
        "As combinações de ano e competição "
        "não correspondem às nove esperadas."
    )

if quantidade_brasileirao != 60:
    raise ValueError(
        "Esperados 60 registros do Brasileirão."
    )

print("\nTodas as validações foram concluídas!")

# 5. ARMAZENAR NO DATABRICKS

df_historico_extra.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("stg_resultados_historicos_extra")

print(
    "\nTabela stg_resultados_historicos_extra "
    "criada com sucesso!"
)