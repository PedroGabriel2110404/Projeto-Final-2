df_completo = spark.sql("""
    SELECT
        b.id_api_clube,
        b.clube,
        b.ano,
        b.posicao_final,
        b.pontos,
        cb.fase_alcancada AS fase_copa_brasil,
        lib.fase_alcancada AS fase_libertadores

    FROM resultados_brasileirao b

    LEFT JOIN resultados_copas cb
        ON b.id_api_clube = cb.id_api_clube
        AND b.ano = cb.ano
        AND cb.competicao = 'Copa do Brasil'

    LEFT JOIN resultados_copas lib
        ON b.id_api_clube = lib.id_api_clube
        AND b.ano = lib.ano
        AND lib.competicao = 'Libertadores'

    ORDER BY b.ano, b.posicao_final
""")

# Verifica a quantidade de registros
total = df_completo.count()

if total != 60:
    raise ValueError(
        f"Esperados 60 registros, mas foram encontrados {total}."
    )

# Salva como tabela Delta
df_completo.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("resultado_completo")

print("Tabela resultado_completo criada com sucesso!")

display(df_completo)
