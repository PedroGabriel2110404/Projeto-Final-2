SELECT
    id_clube,
    nome_clube,
    ano,
    compras_milhoes_brl,
    vendas_milhoes_brl,
    ROUND(
         vendas_milhoes_brl - compras_milhoes_brl,
         2
    ) AS saldo_transferencias_milhoes_brl,
    pontos,
    posicao_final
    FROM workspace.pf1.`vw_analise_clubes_2020_2025`
WHERE compras_milhoes_brl IS NOT NULL
  AND vendas_milhoes_brl IS NOT NULL
  AND pontos IS NOT NULL
ORDER BY ano, saldo_transferencias_milhoes_brl DESC;
