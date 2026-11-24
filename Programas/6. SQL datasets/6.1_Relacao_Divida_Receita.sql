SELECT
    nome_clube,
    ano,
    pontos,
    posicao_final,
    ROUND(
        divida_reportada_milhoes_brl /
        NULLIF(receita_total_milhoes_brl, 0),
        3
    ) AS divida_sobre_receita
FROM workspace.pf1.`vw_analise_clubes_2020_2025`
WHERE receita_total_milhoes_brl > 0
  AND divida_reportada_milhoes_brl IS NOT NULL;
