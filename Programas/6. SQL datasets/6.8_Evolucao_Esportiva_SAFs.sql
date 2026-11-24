WITH clubes_saf AS (
    SELECT
        id_clube,
        COALESCE(
            MIN(data_entrada_saf),
            MIN(data_troca_controle)
        ) AS data_saf
    FROM workspace.pf1.vw_analise_clubes_2020_2025
    WHERE virou_saf = TRUE
    GROUP BY id_clube
),
base AS (
    SELECT
        v.ano,
        v.nome_clube,
        v.posicao_final,
        v.pontos AS pontos_tabela,
        LOWER(TRIM(v.fase_copa_brasil)) AS copa,
        LOWER(TRIM(v.fase_libertadores)) AS lib,
        YEAR(c.data_saf)
            + CASE
                WHEN MONTH(c.data_saf) >= 11 THEN 1
                ELSE 0
              END AS ano_saf
    FROM workspace.pf1.vw_analise_clubes_2020_2025 v
    INNER JOIN clubes_saf c
        ON c.id_clube = v.id_clube
    WHERE v.ano BETWEEN 2020 AND 2025
      AND c.data_saf IS NOT NULL
      AND YEAR(c.data_saf) BETWEEN 2020 AND 2025
),
pontuacoes AS (
    SELECT
        b.*,
        CASE
            WHEN posicao_final = 1
             AND pontos_tabela BETWEEN 0 AND 114
                THEN 100.0
            WHEN posicao_final BETWEEN 2 AND 20
             AND pontos_tabela BETWEEN 0 AND 114
                THEN ROUND(
                    50.0 * (20.0 - posicao_final) / 19.0
                    + 50.0 * pontos_tabela / 114.0,
                    3
                )
            ELSE NULL
        END AS pontos_brasileirao,
        CASE
            WHEN copa IS NULL OR copa IN (
                '', 'não participou', 'nao participou',
                'não disputou', 'nao disputou',
                'sem participação', 'sem participacao'
            ) THEN 0.0
            WHEN copa IN (
                'quarta fase', '4ª fase', '4a fase'
            ) AND ano <> 2020 THEN NULL
            ELSE TRY_ELEMENT_AT(MAP(
                'primeira fase', 5.0,
                '1ª fase', 5.0,
                '1a fase', 5.0,
                'segunda fase', 10.0,
                '2ª fase', 10.0,
                '2a fase', 10.0,
                'terceira fase', 15.0,
                '3ª fase', 15.0,
                '3a fase', 15.0,
                'quarta fase', 20.0,
                '4ª fase', 20.0,
                '4a fase', 20.0,
                'oitavas de final', 35.0,
                'oitavas', 35.0,
                'quartas de final', 50.0,
                'quartas', 50.0,
                'semifinal', 65.0,
                'semifinais', 65.0,
                'vice-campeão', 80.0,
                'vice-campeao', 80.0,
                'vice campeão', 80.0,
                'vice campeao', 80.0,
                'campeão', 100.0,
                'campeao', 100.0
            ), copa)
        END AS pontos_copa,
        CASE
            WHEN lib IS NULL OR lib IN (
                '', 'não participou', 'nao participou',
                'não disputou', 'nao disputou',
                'sem participação', 'sem participacao'
            ) THEN 0.0
            ELSE TRY_ELEMENT_AT(MAP(
                'pré-libertadores - fase 2', 5.0,
                'pre-libertadores - fase 2', 5.0,
                'pré-libertadores fase 2', 5.0,
                'pre-libertadores fase 2', 5.0,
                'pré-libertadores - fase 3', 10.0,
                'pre-libertadores - fase 3', 10.0,
                'pré-libertadores fase 3', 10.0,
                'pre-libertadores fase 3', 10.0,
                'terceira fase', 10.0,
                'fase de grupos', 20.0,
                'grupos', 20.0,
                'oitavas de final', 35.0,
                'oitavas', 35.0,
                'quartas de final', 50.0,
                'quartas', 50.0,
                'semifinal', 65.0,
                'semifinais', 65.0,
                'vice-campeão', 80.0,
                'vice-campeao', 80.0,
                'vice campeão', 80.0,
                'vice campeao', 80.0,
                'campeão', 100.0,
                'campeao', 100.0
            ), lib)
        END AS pontos_libertadores,
        CASE
            WHEN copa IS NULL OR copa IN (
                '', 'não participou', 'nao participou',
                'não disputou', 'nao disputou',
                'sem participação', 'sem participacao'
            ) THEN 0 ELSE 1
        END AS participou_copa,
        CASE
            WHEN lib IS NULL OR lib IN (
                '', 'não participou', 'nao participou',
                'não disputou', 'nao disputou',
                'sem participação', 'sem participacao'
            ) THEN 0 ELSE 1
        END AS participou_libertadores
    FROM base b
),
ide AS (
    SELECT
        ano,
        nome_clube,
        ano_saf,
        CASE
            WHEN pontos_brasileirao IS NULL
              OR (
                  participou_copa = 1
                  AND pontos_copa IS NULL
              )
              OR (
                  participou_libertadores = 1
                  AND pontos_libertadores IS NULL
              )
                THEN NULL

            ELSE ROUND(
                CASE
                    WHEN participou_copa = 1
                     AND participou_libertadores = 1
                        THEN 0.35 * pontos_brasileirao
                           + 0.25 * pontos_copa
                           + 0.40 * pontos_libertadores

                    WHEN participou_libertadores = 1
                        THEN 0.45 * pontos_brasileirao
                           + 0.55 * pontos_libertadores

                    WHEN participou_copa = 1
                        THEN 0.65 * pontos_brasileirao
                           + 0.35 * pontos_copa

                    ELSE pontos_brasileirao
                END,
                3
            )
        END AS ide_real
    FROM pontuacoes
)
SELECT
    ano,
    nome_clube,
    ide_real,
    CASE
        WHEN ano < ano_saf THEN 'Antes da SAF'
        WHEN ano = ano_saf THEN 'Ano de transicao'
        ELSE 'Depois da SAF'
    END AS periodo_saf
FROM ide
ORDER BY nome_clube, ano;
