from pyspark.sql import functions as F

ANOS = (2022, 2023, 2024)
DESTINO = "resultado_completo"

# 1. Carregar tabelas criadas na extração API.
brasileirao = spark.table("resultados_brasileirao")
copas = spark.table("resultados_copas")

# 2. Conferir as colunas necessárias.
colunas_brasileirao = {"id_api_clube", "clube", "ano", "posicao_final", "pontos"}
colunas_copas = {"id_api_clube", "ano", "competicao", "fase_alcancada"}

for nome, df, obrigatorias in (
    ("resultados_brasileirao", brasileirao, colunas_brasileirao),
    ("resultados_copas", copas, colunas_copas),
):
    faltantes = sorted(obrigatorias - set(df.columns))
    if faltantes:
        raise ValueError(f"{nome}: faltam as colunas {faltantes}")

# 3. Selecionar apenas as temporadas do recorte da API.
brasileirao = (
    brasileirao
    .filter(F.col("ano").isin(*ANOS))
    .select(
        F.col("id_api_clube").cast("int").alias("id_api_clube"),
        F.col("clube").cast("string").alias("clube"),
        F.col("ano").cast("int").alias("ano"),
        F.col("posicao_final").cast("int").alias("posicao_final"),
        F.col("pontos").cast("int").alias("pontos"),
    )
)

copas = (
    copas
    .filter(F.col("ano").isin(*ANOS))
    .select(
        F.col("id_api_clube").cast("int").alias("id_api_clube"),
        F.col("ano").cast("int").alias("ano"),
        F.col("competicao").cast("string").alias("competicao"),
        F.col("fase_alcancada").cast("string").alias("fase_alcancada"),
    )
)

# 4. Validar chaves únicas antes dos JOINs para evitar multiplicar linhas.
def validar_unicidade(df, chaves, descricao):
    duplicados = (
        df.groupBy(*chaves).count().filter(F.col("count") > 1)
    )
    if duplicados.limit(1).count():
        display(duplicados)
        raise ValueError(f"Duplicidades em {descricao}: {chaves}")

validar_unicidade(brasileirao, ["ano", "id_api_clube"], "Brasileirão")
validar_unicidade(copas, ["ano", "id_api_clube", "competicao"], "Copas")

valores_invalidos = copas.filter(
    ~F.col("competicao").isin("Copa do Brasil", "Libertadores")
    | F.col("fase_alcancada").isNull()
)
if valores_invalidos.limit(1).count():
    display(valores_invalidos)
    raise ValueError("Há competições desconhecidas ou fases nulas nas copas")

# 5. Fazer uma junção por competição, preservando todos os clubes da Série A.
copa_brasil = (
    copas.filter(F.col("competicao") == "Copa do Brasil")
    .select("id_api_clube", "ano", F.col("fase_alcancada").alias("fase_copa_brasil"))
)
libertadores = (
    copas.filter(F.col("competicao") == "Libertadores")
    .select("id_api_clube", "ano", F.col("fase_alcancada").alias("fase_libertadores"))
)

df_completo = (
    brasileirao
    .join(copa_brasil, ["id_api_clube", "ano"], "left")
    .join(libertadores, ["id_api_clube", "ano"], "left")
    .select(
        "id_api_clube", "clube", "ano", "posicao_final", "pontos",
        "fase_copa_brasil", "fase_libertadores"
    )
)

# 6. Validar o resultado antes de sobrescrever qualquer tabela.
resumo = df_completo.groupBy("ano").agg(
    F.count("*").alias("clubes"),
    F.count("posicao_final").alias("com_posicao"),
    F.count("fase_copa_brasil").alias("com_copa_brasil"),
    F.count("fase_libertadores").alias("com_libertadores"),
).orderBy("ano")

print("Registros por temporada:")
display(resumo)

quantidades = {linha["ano"]: linha["clubes"] for linha in resumo.collect()}
if quantidades != {ano: 20 for ano in ANOS}:
    raise ValueError(f"Esperados 20 clubes em cada ano: {quantidades}")

obrigatorios_nulos = df_completo.filter(
    F.col("id_api_clube").isNull()
    | F.col("clube").isNull()
    | (F.trim(F.col("clube")) == "")
    | F.col("ano").isNull()
    | F.col("posicao_final").isNull()
    | F.col("pontos").isNull()
)
if obrigatorios_nulos.limit(1).count():
    display(obrigatorios_nulos)
    raise ValueError("Existem campos obrigatórios nulos na mescla")

validar_unicidade(df_completo, ["ano", "id_api_clube"], "Resultado consolidado")

# 7. Criar a tabela intermediária consumida pelo código 3.2.
df_completo.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(DESTINO)

print(f"Tabela {DESTINO} criada com sucesso ({df_completo.count()} registros).")
display(df_completo.orderBy("ano", "posicao_final"))
