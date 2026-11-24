# Remove colunas auxiliares da transformação
df_final = df_copas.drop(
    columns=["ordem"],
    errors="ignore"
)

# Converte para Spark
df_spark = spark.createDataFrame(df_final)

# Salva os dados como tabela Delta
df_spark.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("resultados_copas")

print("Tabela criada com sucesso!")
