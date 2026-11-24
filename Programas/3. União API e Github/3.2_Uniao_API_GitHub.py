import re
import unicodedata

from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from pyspark.sql.window import Window

ANOS_GITHUB = (2020, 2021, 2025)
ANOS_API = (2022, 2023, 2024)
ANOS_TODOS = (*ANOS_GITHUB, *ANOS_API)

ALIAS = {
    "atleticomineiro": "atleticomg",
    "atleticoparanaense": "athleticopr",
    "athleticoparanaense": "athleticopr",
    "atleticopr": "athleticopr",
    "redbullbragantino": "bragantino",
    "rbbragantino": "bragantino",
    "americamineiro": "americamg",
    "vascodagama": "vasco",
    "crvascodagama": "vasco",
    "gremiofbpa": "gremio",
    "saopaulofc": "saopaulo",
    "botafogofr": "botafogo",
    "fortalezaec": "fortaleza",
    "atleticogoianiense": "atleticogo",
}

# Ordem de progresso: a etapa preliminar deve ficar abaixo da fase de grupos.
ORDEM_FASES = {
    "Pré-Libertadores - Fase 1": 1,
    "Pré-Libertadores - Fase 2": 2,
    "Pré-Libertadores - Fase 3": 3,
    "Primeira fase": 10,
    "Segunda fase": 20,
    "Terceira fase": 30,
    "Quarta fase": 40,
    "16 avos de final": 45,
    "Fase de grupos": 46,
    "Oitavas de final": 50,
    "Quartas de final": 60,
    "Semifinal": 70,
    "Finalista": 80,
    "Vice-campeão": 80,
    "Campeão": 90,
}


def normalizar(nome):
    if nome is None:
        return None
    texto = re.sub(r"\s*\(BRA\)\s*$", "", str(nome), flags=re.IGNORECASE)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]", "", texto.lower())
    return ALIAS.get(texto, texto)


normalizar_udf = F.udf(normalizar, StringType())


def validar_colunas(df, colunas, origem):
    faltantes = sorted(set(colunas).difference(df.columns))
    if faltantes:
        raise ValueError(f"{origem}: faltam colunas {faltantes}")


def validar_chaves_unicas(df, chaves, descricao):
    duplicados = (
        df.groupBy(*chaves)
        .count()
        .filter(F.col("count") > 1)
    )
    if duplicados.limit(1).count():
        display(duplicados)
        raise ValueError(f"{descricao}: chaves duplicadas {chaves}")


# ==================================================================
# 1. CARREGAR AS DUAS FONTES JA PROCESSADAS
# ==================================================================
api_bruta = spark.table("resultado_completo")
historico = spark.table("stg_resultados_historicos_extra")

colunas_api = [
    "id_api_clube", "clube", "ano", "posicao_final", "pontos",
    "fase_copa_brasil", "fase_libertadores",
]
colunas_historico = [
    "clube", "ano", "competicao", "posicao_final", "pontos",
    "fase_alcancada",
]
validar_colunas(api_bruta, colunas_api, "resultado_completo")
validar_colunas(historico, colunas_historico, "stg_resultados_historicos_extra")

api = (
    api_bruta
    .filter(F.col("ano").isin(*ANOS_API))
    .select(
        F.col("id_api_clube").cast("int").alias("id_api_clube"),
        F.col("clube").cast("string").alias("clube"),
        F.col("ano").cast("int").alias("ano"),
        F.col("posicao_final").cast("int").alias("posicao_final"),
        F.col("pontos").cast("int").alias("pontos"),
        F.col("fase_copa_brasil").cast("string").alias("fase_copa_brasil"),
        F.col("fase_libertadores").cast("string").alias("fase_libertadores"),
    )
    .withColumn("chave_clube", normalizar_udf(F.col("clube")))
    .withColumn("origem_dados", F.lit("API-Football"))
)

historico = (
    historico
    .filter(F.col("ano").isin(*ANOS_GITHUB))
    .select(
        F.col("clube").cast("string").alias("clube"),
        F.col("ano").cast("int").alias("ano"),
        F.col("competicao").cast("string").alias("competicao"),
        F.col("posicao_final").cast("int").alias("posicao_final"),
        F.col("pontos").cast("int").alias("pontos"),
        F.col("fase_alcancada").cast("string").alias("fase_alcancada"),
    )
    .withColumn("chave_clube", normalizar_udf(F.col("clube")))
)

# ==================================================================
# 2. TRANSFORMAR O HISTORICO EM UMA LINHA POR CLUBE/ANO
# ==================================================================
br = historico.filter(F.col("competicao") == "Brasileirão")
copa = historico.filter(F.col("competicao") == "Copa do Brasil")
lib = historico.filter(F.col("competicao") == "Libertadores")

validar_chaves_unicas(br, ["ano", "chave_clube"], "Brasileirão histórico")

mapa_fases = F.create_map(
    *[F.lit(item) for par in ORDEM_FASES.items() for item in par]
)


def selecionar_campanha(tabela, descricao, coluna_saida):
    sem_fase = tabela.filter(
        F.col("fase_alcancada").isNull()
        | ~F.col("fase_alcancada").isin(*ORDEM_FASES.keys())
    )
    if sem_fase.limit(1).count():
        display(sem_fase.select("ano", "clube", "fase_alcancada"))
        raise ValueError(f"{descricao}: existem fases não reconhecidas")

    # Unifica grafias alternativas para um mesmo clube/ano; preserva a melhor fase.
    janela = Window.partitionBy("ano", "chave_clube").orderBy(
        F.col("_ordem_fase").desc(), F.col("clube").asc()
    )
    return (
        tabela
        .withColumn("_ordem_fase", mapa_fases[F.col("fase_alcancada")])
        .withColumn("_rn", F.row_number().over(janela))
        .filter(F.col("_rn") == 1)
        .select("ano", "chave_clube", F.col("fase_alcancada").alias(coluna_saida))
    )


copa_fases = selecionar_campanha(copa, "Copa do Brasil", "fase_copa_brasil")
lib_fases = selecionar_campanha(lib, "Libertadores", "fase_libertadores")

historico_clubes = (
    br.select("clube", "ano", "chave_clube", "posicao_final", "pontos")
    .join(copa_fases, ["ano", "chave_clube"], "left")
    .join(lib_fases, ["ano", "chave_clube"], "left")
    .withColumn("id_api_clube", F.lit(None).cast("int"))
    .withColumn("origem_dados", F.lit("GitHub"))
)

colunas_uniao = [
    "id_api_clube", "clube", "ano", "posicao_final", "pontos",
    "fase_copa_brasil", "fase_libertadores", "chave_clube", "origem_dados",
]

unificado = api.select(*colunas_uniao).unionByName(
    historico_clubes.select(*colunas_uniao)
)

# ==================================================================
# 3. ASSOCIAR OS IDS OFICIAIS A TODOS OS ANOS
# ==================================================================
ids_api = (
    api.select(
        "chave_clube", F.col("id_api_clube").alias("id_clube")
    )
    .filter(F.col("id_clube").isNotNull())
    .distinct()
)

# IDs que foram confirmados no levantamento do projeto e não aparecem
# na amostra do Brasileirão 2022–2024 obtida pela API.
ids_complementares = spark.createDataFrame(
    [("chapecoense", 132), ("mirassol", 7848), ("sport", 123)],
    "chave_clube string, id_clube int",
)

mapa_ids = ids_api.unionByName(ids_complementares).distinct()

conflitos = (
    mapa_ids.groupBy("chave_clube")
    .agg(F.countDistinct("id_clube").alias("quantidade_ids"))
    .filter(F.col("quantidade_ids") > 1)
)
if conflitos.limit(1).count():
    display(conflitos)
    raise ValueError("Há clubes com IDs diferentes entre API e complementos")

# Remover repeticoes exatas antes do JOIN, evitando multiplicacao de linhas.
mapa_ids = mapa_ids.dropDuplicates(["chave_clube"])

integrado = unificado.join(mapa_ids, "chave_clube", "left")

# ==================================================================
# 4. VALIDACOES ANTES DE GRAVAR
# ==================================================================
campos_obrigatorios = [
    "id_clube", "clube", "ano", "posicao_final", "pontos", "chave_clube",
]
nulos = integrado.filter(
    F.col("id_clube").isNull()
    | F.col("chave_clube").isNull()
    | (F.col("chave_clube") == "")
    | F.col("posicao_final").isNull()
    | F.col("pontos").isNull()
    | F.col("clube").isNull()
)
if nulos.limit(1).count():
    display(nulos.select(*campos_obrigatorios, "origem_dados"))
    raise ValueError("Há clubes sem ID oficial ou com campos obrigatórios ausentes")

validar_chaves_unicas(integrado, ["ano", "chave_clube"], "Base integrada")
validar_chaves_unicas(integrado, ["ano", "id_clube"], "IDs da base integrada")

resumo = integrado.groupBy("ano").agg(
    F.count("*").alias("clubes"),
    F.count("posicao_final").alias("com_posicao"),
    F.count("fase_copa_brasil").alias("com_copa_brasil"),
    F.count("fase_libertadores").alias("com_libertadores"),
).orderBy("ano")

print("Resumo por temporada:")
display(resumo)

linhas_resumo = {r["ano"]: r["clubes"] for r in resumo.collect()}
if set(linhas_resumo) != set(ANOS_TODOS) or any(
    linhas_resumo[ano] != 20 for ano in ANOS_TODOS
):
    raise ValueError(f"Esperados 20 clubes por ano (2020–2025): {linhas_resumo}")

if integrado.count() != 120:
    raise ValueError("O resultado integrado precisa ter exatamente 120 registros")

# ==================================================================
# 5. TABELA FINAL DE RESULTADOS ESPORTIVOS
# ==================================================================
# A chave oficial e usada no esquema final (sem a coluna textual "clube").
# A coluna 'clube' continua disponivel no DataFrame integrado para auditoria.
# Os campos detalhados das partidas tambem nao integram o modelo final.
colunas_finais = [
    "id_clube", "ano", "posicao_final", "pontos",
    "fase_copa_brasil", "fase_libertadores", "origem_dados",
]
resultado = integrado.select(*colunas_finais).orderBy("ano", "posicao_final")

resultado.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("resultados_esportivos")

print("Tabela resultados_esportivos criada com sucesso: 120 registros.")
display(resultado)
