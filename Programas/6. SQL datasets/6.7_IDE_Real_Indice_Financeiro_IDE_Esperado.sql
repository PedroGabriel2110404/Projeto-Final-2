WITH
base AS (
    SELECT
        v.ano, v.id_clube, v.nome_clube,
        v.posicao_final, v.pontos AS pontos_tabela,
        v.fase_copa_brasil, v.fase_libertadores,
        COALESCE(LOWER(TRIM(v.fase_copa_brasil)), '') AS copa_norm,
        COALESCE(LOWER(TRIM(v.fase_libertadores)), '') AS lib_norm,
        CAST(v.receita_total_milhoes_brl AS DOUBLE) AS receita,
        CAST(v.gastos_pessoal_milhoes_brl AS DOUBLE) AS gastos,
        CAST(v.valor_elenco_milhoes_eur AS DOUBLE) AS elenco,
        CAST(v.compras_milhoes_brl AS DOUBLE) AS compras,
        CAST(v.vendas_milhoes_brl AS DOUBLE) AS vendas,
        CAST(v.divida_reportada_milhoes_brl AS DOUBLE) AS divida,
        CAST(v.gastos_pessoal_milhoes_brl AS DOUBLE) AS investimento_milhoes
    FROM workspace.pf1.vw_analise_clubes_2020_2025 v
    WHERE v.ano BETWEEN 2020 AND 2025
),
pontuacoes AS (
    SELECT b.*,
        CASE
            WHEN b.posicao_final = 1 AND b.pontos_tabela BETWEEN 0 AND 114
                THEN 100.0
            WHEN b.posicao_final BETWEEN 2 AND 20
             AND b.pontos_tabela BETWEEN 0 AND 114
                THEN ROUND(50.0 * (20.0 - b.posicao_final) / 19.0
                         + 50.0 * b.pontos_tabela / 114.0, 3)
            ELSE NULL
        END AS pontos_brasileirao,
        CASE
            WHEN copa_norm IN ('', 'não participou', 'nao participou',
                               'não disputou', 'nao disputou',
                               'sem participação', 'sem participacao') THEN 0.0
            WHEN copa_norm IN ('primeira fase', '1ª fase', '1a fase') THEN 5.0
            WHEN copa_norm IN ('segunda fase', '2ª fase', '2a fase') THEN 10.0
            WHEN copa_norm IN ('terceira fase', '3ª fase', '3a fase') THEN 15.0
            WHEN ano = 2020
             AND copa_norm IN ('quarta fase', '4ª fase', '4a fase') THEN 20.0
            WHEN copa_norm IN ('oitavas de final', 'oitavas') THEN 35.0
            WHEN copa_norm IN ('quartas de final', 'quartas') THEN 50.0
            WHEN copa_norm IN ('semifinal', 'semifinais') THEN 65.0
            WHEN copa_norm IN ('vice-campeão', 'vice-campeao',
                               'vice campeão', 'vice campeao') THEN 80.0
            WHEN copa_norm IN ('campeão', 'campeao') THEN 100.0
            ELSE NULL
        END AS pontos_copa,
        CASE
            WHEN lib_norm IN ('', 'não participou', 'nao participou',
                              'não disputou', 'nao disputou',
                              'sem participação', 'sem participacao') THEN 0.0
            WHEN lib_norm IN ('pré-libertadores - fase 2', 'pre-libertadores - fase 2',
                              'pré-libertadores fase 2', 'pre-libertadores fase 2') THEN 5.0
            WHEN lib_norm IN ('pré-libertadores - fase 3', 'pre-libertadores - fase 3',
                              'pré-libertadores fase 3', 'pre-libertadores fase 3',
                              'terceira fase') THEN 10.0
            WHEN lib_norm IN ('fase de grupos', 'grupos') THEN 20.0
            WHEN lib_norm IN ('oitavas de final', 'oitavas') THEN 35.0
            WHEN lib_norm IN ('quartas de final', 'quartas') THEN 50.0
            WHEN lib_norm IN ('semifinal', 'semifinais') THEN 65.0
            WHEN lib_norm IN ('vice-campeão', 'vice-campeao',
                              'vice campeão', 'vice campeao') THEN 80.0
            WHEN lib_norm IN ('campeão', 'campeao') THEN 100.0
            ELSE NULL
        END AS pontos_libertadores,
        CASE WHEN copa_norm IN ('', 'não participou', 'nao participou',
                                'não disputou', 'nao disputou',
                                'sem participação', 'sem participacao')
             THEN 0 ELSE 1 END AS participou_copa,
        CASE WHEN lib_norm IN ('', 'não participou', 'nao participou',
                               'não disputou', 'nao disputou',
                               'sem participação', 'sem participacao')
             THEN 0 ELSE 1 END AS participou_libertadores
    FROM base b
),
esportivo AS (
    SELECT p.*,
        CASE
            WHEN p.pontos_brasileirao IS NULL
              OR (p.participou_libertadores = 1 AND p.pontos_libertadores IS NULL)
              OR (p.participou_copa = 1 AND p.pontos_copa IS NULL)
                THEN NULL
            ELSE ROUND(CASE
                WHEN p.participou_libertadores = 1 AND p.participou_copa = 1
                    THEN 0.35 * p.pontos_brasileirao
                       + 0.40 * p.pontos_libertadores + 0.25 * p.pontos_copa
                WHEN p.participou_libertadores = 1 AND p.participou_copa = 0
                    THEN 0.45 * p.pontos_brasileirao + 0.55 * p.pontos_libertadores
                WHEN p.participou_libertadores = 0 AND p.participou_copa = 1
                    THEN 0.65 * p.pontos_brasileirao + 0.35 * p.pontos_copa
                ELSE p.pontos_brasileirao
            END, 3)
        END AS ide_real
    FROM pontuacoes p
),
indicadores AS (
    SELECT e.ano, e.id_clube, e.ide_real, t.indicador, t.valor
    FROM esportivo e
    LATERAL VIEW STACK(5,
        'Receita', e.receita,
        'Gastos', e.gastos,
        'Elenco', e.elenco,
        'Contratacoes', e.compras,
        'Vendas', e.vendas
    ) t AS indicador, valor
),
postos_financeiros AS (
    SELECT ano, id_clube, indicador,
        PERCENT_RANK() OVER (
            PARTITION BY ano, indicador ORDER BY valor ASC
        ) AS percentil
    FROM indicadores
    WHERE valor IS NOT NULL
),
indicadores_normalizados AS (
    SELECT i.ano, i.id_clube, i.ide_real, i.indicador, p.percentil
    FROM indicadores i
    LEFT JOIN postos_financeiros p
      ON p.ano = i.ano
     AND p.id_clube = i.id_clube
     AND p.indicador = i.indicador
),
anos AS (SELECT DISTINCT ano FROM esportivo),
pares_treino AS (
    SELECT a.ano AS ano_avaliado, i.indicador, i.percentil, i.ide_real
    FROM anos a
    INNER JOIN indicadores_normalizados i
      ON i.ano <> a.ano
    WHERE i.percentil IS NOT NULL AND i.ide_real IS NOT NULL
),
postos_treino AS (
    SELECT ano_avaliado, indicador,
        RANK() OVER (
            PARTITION BY ano_avaliado, indicador ORDER BY percentil
        ) + (COUNT(*) OVER (
            PARTITION BY ano_avaliado, indicador, percentil
        ) - 1) / 2.0 AS posto_financeiro,
        RANK() OVER (
            PARTITION BY ano_avaliado, indicador ORDER BY ide_real
        ) + (COUNT(*) OVER (
            PARTITION BY ano_avaliado, indicador, ide_real
        ) - 1) / 2.0 AS posto_esportivo
    FROM pares_treino
),
correlacoes_if AS (
    SELECT ano_avaliado, indicador,
           CORR(posto_financeiro, posto_esportivo) AS rho_ide
    FROM postos_treino
    GROUP BY ano_avaliado, indicador
),
pesos_brutos AS (
    SELECT a.ano AS ano_avaliado, f.indicador, c.rho_ide,
        COALESCE(GREATEST(c.rho_ide, 0.0), 0.0) AS forca_positiva
    FROM anos a
    CROSS JOIN (SELECT DISTINCT indicador FROM indicadores) f
    LEFT JOIN correlacoes_if c
      ON c.ano_avaliado = a.ano AND c.indicador = f.indicador
),
pesos_totais AS (
    SELECT *, SUM(forca_positiva) OVER (
        PARTITION BY ano_avaliado
    ) AS soma_positiva
    FROM pesos_brutos
),
pesos AS (
    SELECT ano_avaliado, indicador, rho_ide,
        CASE WHEN soma_positiva > 0.0
             THEN forca_positiva / soma_positiva
             ELSE 0.2 END AS peso
    FROM pesos_totais
),
indice_financeiro AS (
    SELECT w.ano_avaliado, i.ano, i.id_clube,
        ROUND(SUM(COALESCE(i.percentil, 0.5) * w.peso), 6) AS indice_financeiro,
        COUNT(i.percentil) AS fatores_disponiveis
    FROM pesos w
    INNER JOIN indicadores_normalizados i
      ON i.indicador = w.indicador
    GROUP BY w.ano_avaliado, i.ano, i.id_clube
),
pesos_visiveis AS (
    SELECT ano_avaliado,
        MAX(CASE WHEN indicador = 'Receita' THEN peso END) AS peso_receita,
        MAX(CASE WHEN indicador = 'Gastos' THEN peso END) AS peso_gastos,
        MAX(CASE WHEN indicador = 'Elenco' THEN peso END) AS peso_elenco,
        MAX(CASE WHEN indicador = 'Contratacoes' THEN peso END) AS peso_contratacoes,
        MAX(CASE WHEN indicador = 'Vendas' THEN peso END) AS peso_vendas,
        MAX(CASE WHEN indicador = 'Receita' THEN rho_ide END) AS rho_receita,
        MAX(CASE WHEN indicador = 'Gastos' THEN rho_ide END) AS rho_gastos,
        MAX(CASE WHEN indicador = 'Elenco' THEN rho_ide END) AS rho_elenco,
        MAX(CASE WHEN indicador = 'Contratacoes' THEN rho_ide END) AS rho_contratacoes,
        MAX(CASE WHEN indicador = 'Vendas' THEN rho_ide END) AS rho_vendas
    FROM pesos
    GROUP BY ano_avaliado
),
dados_modelo AS (
    SELECT f.ano_avaliado, e.*, f.indice_financeiro, f.fatores_disponiveis
    FROM indice_financeiro f
    INNER JOIN esportivo e
      ON e.ano = f.ano AND e.id_clube = f.id_clube
),
modelos AS (
    SELECT ano_avaliado,
        REGR_INTERCEPT(ide_real, indice_financeiro) AS alfa,
        REGR_SLOPE(ide_real, indice_financeiro) AS beta,
        COUNT(ide_real) AS observacoes_treino
    FROM dados_modelo
    WHERE ano <> ano_avaliado
      AND ide_real IS NOT NULL
      AND indice_financeiro IS NOT NULL
    GROUP BY ano_avaliado
),
previsoes AS (
    SELECT d.*, m.alfa, m.beta, m.observacoes_treino,
        w.peso_receita, w.peso_gastos, w.peso_elenco,
        w.peso_contratacoes, w.peso_vendas,
        w.rho_receita, w.rho_gastos, w.rho_elenco,
        w.rho_contratacoes, w.rho_vendas,
        ROUND(m.alfa + m.beta * d.indice_financeiro, 3) AS ide_esperado
    FROM dados_modelo d
    INNER JOIN modelos m ON d.ano_avaliado = m.ano_avaliado
    INNER JOIN pesos_visiveis w ON d.ano_avaliado = w.ano_avaliado
    WHERE d.ano = d.ano_avaliado
),
rankings AS (
    SELECT p.*,
        ROW_NUMBER() OVER (
            PARTITION BY p.ano ORDER BY p.ide_real DESC NULLS LAST, p.id_clube
        ) AS ranking_esportivo_real,
        ROW_NUMBER() OVER (
            PARTITION BY p.ano ORDER BY p.ide_esperado DESC NULLS LAST, p.id_clube
        ) AS ranking_esportivo_esperado,
        CASE WHEN p.ide_real IS NOT NULL THEN ROW_NUMBER() OVER (
            PARTITION BY p.ano ORDER BY p.ide_real ASC NULLS LAST, p.id_clube
        ) END AS ranking_bottom_real,
        CASE WHEN p.ide_esperado IS NOT NULL THEN ROW_NUMBER() OVER (
            PARTITION BY p.ano ORDER BY p.ide_esperado ASC NULLS LAST, p.id_clube
        ) END AS ranking_bottom_esperado
    FROM previsoes p
),
resultados AS (
    SELECT r.ano, r.id_clube, r.nome_clube, r.posicao_final,
        r.pontos_tabela AS pontos_serie_a,
        r.fase_copa_brasil, r.fase_libertadores,
        r.participou_copa, r.participou_libertadores,
        ROUND(r.pontos_brasileirao, 3) AS pontos_brasileirao,
        ROUND(r.pontos_copa, 3) AS pontos_copa,
        ROUND(r.pontos_libertadores, 3) AS pontos_libertadores,
        r.ide_real, r.ide_esperado,
        ROUND(r.ide_real - r.ide_esperado, 3) AS desvio_ide,
        r.ranking_esportivo_real, r.ranking_esportivo_esperado,
        r.ranking_bottom_real, r.ranking_bottom_esperado,
        r.ranking_esportivo_esperado - r.ranking_esportivo_real AS desvio_ranking,
        CASE WHEN r.ide_real IS NULL OR r.ide_esperado IS NULL THEN 'Sem dados'
             WHEN r.ide_real > r.ide_esperado THEN 'Acima do esperado'
             WHEN r.ide_real < r.ide_esperado THEN 'Abaixo do esperado'
             ELSE 'Igual ao esperado' END AS diagnostico,
        r.indice_financeiro, r.fatores_disponiveis,
        r.observacoes_treino, r.alfa, r.beta, r.investimento_milhoes,
        r.receita AS receita_milhoes,
        r.gastos AS gastos_pessoal_milhoes,
        r.elenco AS valor_elenco_milhoes_eur,
        r.compras AS contratacoes_milhoes,
        r.vendas AS vendas_milhoes,
        r.divida AS divida_milhoes,
        ROUND(r.peso_receita, 4) AS peso_receita,
        ROUND(r.peso_gastos, 4) AS peso_gastos,
        ROUND(r.peso_elenco, 4) AS peso_elenco,
        ROUND(r.peso_contratacoes, 4) AS peso_contratacoes,
        ROUND(r.peso_vendas, 4) AS peso_vendas,
        ROUND(r.rho_receita, 4) AS rho_receita,
        ROUND(r.rho_gastos, 4) AS rho_gastos,
        ROUND(r.rho_elenco, 4) AS rho_elenco,
        ROUND(r.rho_contratacoes, 4) AS rho_contratacoes,
        ROUND(r.rho_vendas, 4) AS rho_vendas
    FROM rankings r
),
metricas_erro AS (
    SELECT r.*,
        AVG(ABS(r.desvio_ide)) OVER () AS mae_geral_bruto,
        AVG(ABS(r.desvio_ide)) OVER (PARTITION BY r.ano) AS mae_ano_bruto
    FROM resultados r
)
SELECT r.*,
    CASE WHEN r.ide_real IS NOT NULL AND r.ranking_esportivo_real <= 5
         THEN 'Sim' ELSE 'Nao' END AS top5_real,
    CASE WHEN r.ide_esperado IS NOT NULL AND r.ranking_esportivo_esperado <= 5
         THEN 'Sim' ELSE 'Nao' END AS top5_esperado,
    CASE WHEN r.ranking_bottom_real <= 5 THEN 'Sim' ELSE 'Nao' END AS bottom5_real,
    CASE WHEN r.ranking_bottom_esperado <= 5 THEN 'Sim' ELSE 'Nao' END AS bottom5_esperado,
    ROUND(r.mae_geral_bruto, 3) AS mae_geral,
    ROUND(r.mae_ano_bruto, 3) AS mae_ano,
    ROUND(r.mae_geral_bruto, 2) AS margem_tolerancia,
    CASE WHEN r.desvio_ide IS NOT NULL AND r.mae_geral_bruto > 0
         THEN ROUND(r.desvio_ide / r.mae_geral_bruto, 3)
         ELSE NULL END AS desvio_em_mae,
    CASE WHEN r.desvio_ide IS NULL OR r.mae_geral_bruto IS NULL
             THEN 'Sem classificacao'
         WHEN r.desvio_ide > r.mae_geral_bruto THEN 'Superou as expectativas'
         WHEN r.desvio_ide < -r.mae_geral_bruto THEN 'Abaixo das expectativas'
         ELSE 'Atendeu as expectativas'
    END AS classificacao_expectativa,
    CASE WHEN r.desvio_ide IS NULL OR r.mae_geral_bruto IS NULL
             THEN 'Sem classificacao'
         WHEN r.desvio_ide > 2.0 * r.mae_geral_bruto
             THEN 'Superou muito as expectativas'
         WHEN r.desvio_ide > r.mae_geral_bruto THEN 'Acima do esperado'
         WHEN r.desvio_ide < -2.0 * r.mae_geral_bruto
             THEN 'Muito abaixo das expectativas'
         WHEN r.desvio_ide < -r.mae_geral_bruto THEN 'Abaixo do esperado'
         ELSE 'Dentro do esperado'
    END AS classificacao_expectativa_detalhada,
    ROUND(CORR(r.investimento_milhoes, r.ide_real) OVER (), 3) AS correlacao_geral,
    ROUND(CORR(r.investimento_milhoes, r.ide_real) OVER (PARTITION BY r.ano), 3)
        AS correlacao_ano
FROM metricas_erro r
ORDER BY r.ano DESC, r.desvio_ide DESC;
