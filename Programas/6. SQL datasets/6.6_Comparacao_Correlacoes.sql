WITH base AS (
    SELECT
        ano, id_clube, posicao_final,
        fase_copa_brasil, fase_libertadores,
        CAST(receita_total_milhoes_brl AS DOUBLE) AS receita,
        CAST(gastos_pessoal_milhoes_brl AS DOUBLE) AS gastos,
        CAST(valor_elenco_milhoes_eur AS DOUBLE) AS elenco,
        CAST(compras_milhoes_brl AS DOUBLE) AS compras,
        CAST(vendas_milhoes_brl AS DOUBLE) AS vendas,
        CAST(divida_reportada_milhoes_brl AS DOUBLE) AS divida
    FROM workspace.pf1.vw_analise_clubes_2020_2025
    WHERE ano BETWEEN 2020 AND 2025
),
calculos AS (
    SELECT
        b.*,
        CASE
            WHEN receita IS NOT NULL
             AND gastos IS NOT NULL
             AND divida IS NOT NULL
            THEN (receita - gastos) /
                 (1.0 + GREATEST(divida, 0.0))
        END AS controle_dividas,
        CASE WHEN receita > 0
            THEN gastos / receita
        END AS comprometimento_receita_pessoal,
        CASE WHEN receita > 0 AND divida >= 0
            THEN divida / receita
        END AS endividamento_relativo,
        CASE WHEN receita > 0
            THEN compras / receita
        END AS intensidade_contratacoes,
        TRY_ELEMENT_AT(MAP(
            'Primeira fase', 1,
            'Segunda fase', 2,
            'Terceira fase', 3,
            'Quarta fase', 4,
            'Oitavas de final', 5,
            'Quartas de final', 6,
            'Semifinal', 7,
            'Vice-campeão', 8,
            'Campeão', 9
        ), fase_copa_brasil) AS fase_copa_ordinal,
        TRY_ELEMENT_AT(MAP(
            'Pré-Libertadores - Fase 2', 1,
            'Pré-Libertadores - Fase 3', 2,
            'Terceira fase', 2,
            'Fase de grupos', 3,
            'Oitavas de final', 4,
            'Quartas de final', 5,
            'Semifinal', 6,
            'Vice-campeão', 7,
            'Campeão', 8
        ), fase_libertadores) AS fase_libertadores_ordinal
    FROM base b
),
pares_validos AS (
    SELECT
        c.ano,
        c.id_clube,
        i.indicador,
        i.valor,
        d.competicao,
        d.desempenho
    FROM calculos c
    LATERAL VIEW STACK(9,
        'Receita total', receita,
        'Gastos com pessoal', gastos,
        'Valor de mercado do elenco', elenco,
        'Contratações', compras,
        'Vendas de jogadores', vendas,
        'Controle de Dívidas', controle_dividas,
        'Comprometimento da receita com pessoal',
            comprometimento_receita_pessoal,
        'Endividamento relativo', endividamento_relativo,
        'Intensidade de contratações', intensidade_contratacoes
    ) i AS indicador, valor
    LATERAL VIEW STACK(3,
        'Brasileirão', -CAST(posicao_final AS DOUBLE),
        'Copa do Brasil', CAST(fase_copa_ordinal AS DOUBLE),
        'Libertadores', CAST(fase_libertadores_ordinal AS DOUBLE)
    ) d AS competicao, desempenho
    WHERE i.valor IS NOT NULL
      AND d.desempenho IS NOT NULL
),
postos AS (
    SELECT
        ano,
        indicador,
        competicao,
        RANK() OVER (
            PARTITION BY ano, indicador, competicao
            ORDER BY valor
        ) + (
            COUNT(*) OVER (
                PARTITION BY ano, indicador, competicao, valor
            ) - 1
        ) / 2.0 AS posto_financeiro,
        RANK() OVER (
            PARTITION BY ano, indicador, competicao
            ORDER BY desempenho
        ) + (
            COUNT(*) OVER (
                PARTITION BY ano, indicador, competicao, desempenho
            ) - 1
        ) / 2.0 AS posto_esportivo
    FROM pares_validos
),
correlacoes_anuais AS (
    SELECT
        ano,
        indicador,
        competicao,
        CORR(posto_financeiro, posto_esportivo) AS correlacao
    FROM postos
    GROUP BY ano, indicador, competicao
),
medias_competicao AS (
    SELECT
        indicador,
        competicao,
        AVG(correlacao) AS correlacao_media
    FROM correlacoes_anuais
    GROUP BY indicador, competicao
),
resumo AS (
    SELECT
        indicador,
        ROUND(MAX(
            CASE WHEN competicao = 'Brasileirão'
                 THEN correlacao_media END
        ), 3) AS brasileirao,
        ROUND(MAX(
            CASE WHEN competicao = 'Copa do Brasil'
                 THEN correlacao_media END
        ), 3) AS copa_do_brasil,
        ROUND(MAX(
            CASE WHEN competicao = 'Libertadores'
                 THEN correlacao_media END
        ), 3) AS libertadores,
        ROUND(AVG(correlacao_media), 3) AS media_geral
    FROM medias_competicao
    GROUP BY indicador
),
ranking AS (
    SELECT
        ROW_NUMBER() OVER (
            ORDER BY media_geral DESC, indicador
        ) AS posicao,
        indicador,
        brasileirao,
        copa_do_brasil,
        libertadores,
        media_geral
    FROM resumo
)
SELECT
    posicao,
    CONCAT(
        CAST(posicao AS STRING),
        'º - ',
        indicador
    ) AS indicador_ranking,
    indicador,
    brasileirao,
    copa_do_brasil,
    libertadores,
    media_geral
FROM ranking
ORDER BY posicao;
