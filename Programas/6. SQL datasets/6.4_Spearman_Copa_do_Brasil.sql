WITH base AS (
    SELECT
        ano,
        CASE fase_copa_brasil
            WHEN 'Primeira fase' THEN 1
            WHEN 'Segunda fase' THEN 2
            WHEN 'Terceira fase' THEN 3
            WHEN 'Quarta fase' THEN 4
            WHEN 'Oitavas de final' THEN 5
            WHEN 'Quartas de final' THEN 6
            WHEN 'Semifinal' THEN 7
            WHEN 'Vice-campeão' THEN 8
            WHEN 'Campeão' THEN 9
        END AS fase_ordinal,
        CAST(receita_total_milhoes_brl AS DOUBLE) AS receita,
        CAST(gastos_pessoal_milhoes_brl AS DOUBLE) AS gastos,
        CAST(valor_elenco_milhoes_eur AS DOUBLE) AS elenco,
        CAST(compras_milhoes_brl AS DOUBLE) AS compras,
        CAST(vendas_milhoes_brl AS DOUBLE) AS vendas,
        CAST(divida_reportada_milhoes_brl AS DOUBLE) AS divida
    FROM workspace.pf1.vw_analise_clubes_2020_2025
    WHERE ano BETWEEN 2020 AND 2025
),
pares AS (
    SELECT
        b.ano,
        b.fase_ordinal AS desempenho,
        t.indicador,
        t.valor
    FROM base b
    LATERAL VIEW STACK(6,
        'Receita total', b.receita,
        'Gastos com pessoal', b.gastos,
        'Valor de mercado do elenco', b.elenco,
        'Contratações', b.compras,
        'Vendas de jogadores', b.vendas,
        'Controle de Dívidas',
            CASE
                WHEN b.receita IS NOT NULL
                 AND b.gastos IS NOT NULL
                 AND b.divida IS NOT NULL
                THEN (b.receita - b.gastos) /
                     (1.0 + GREATEST(b.divida, 0.0))
            END
    ) t AS indicador, valor
    WHERE t.valor IS NOT NULL
      AND b.fase_ordinal IS NOT NULL
),
postos AS (
    SELECT
        ano,
        indicador,
        RANK() OVER (
            PARTITION BY ano, indicador ORDER BY valor
        ) + (
            COUNT(*) OVER (
                PARTITION BY ano, indicador, valor
            ) - 1
        ) / 2.0 AS posto_financeiro,
        RANK() OVER (
            PARTITION BY ano, indicador ORDER BY desempenho
        ) + (
            COUNT(*) OVER (
                PARTITION BY ano, indicador, desempenho
            ) - 1
        ) / 2.0 AS posto_esportivo
    FROM pares
)
SELECT
    CAST(ano AS STRING) AS ano,
    indicador,
    COUNT(*) AS quantidade_clubes,
    ROUND(CORR(posto_financeiro, posto_esportivo), 3) AS correlacao
FROM postos
GROUP BY ano, indicador
ORDER BY ano, indicador;
