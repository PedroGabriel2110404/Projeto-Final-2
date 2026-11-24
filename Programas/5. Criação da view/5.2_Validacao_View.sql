-- A. Contagem total e situação geral
WITH estatisticas AS (
  SELECT
    COUNT(*) AS total_registros,
    COUNT(DISTINCT CONCAT(CAST(id_clube AS STRING), ':', CAST(ano AS STRING)))
      AS combinacoes_clube_ano,
    SUM(CASE WHEN nome_clube IS NULL THEN 1 ELSE 0 END)
      AS nomes_ausentes
  FROM workspace.pf1.vw_analise_clubes_2020_2025
)
SELECT *,
  CASE
    WHEN total_registros = 120
     AND combinacoes_clube_ano = 120
     AND nomes_ausentes = 0 THEN 'OK'
    ELSE 'REVISAR'
  END AS situacao
FROM estatisticas;

-- B. Por temporada: esperado 20 linhas e 20 clubes distintos
SELECT
    ano,
    COUNT(*) AS quantidade_registros,
    COUNT(DISTINCT id_clube) AS clubes_distintos,
    COUNT(id_financeiro) AS registros_com_vinculo_financeiro,
    COUNT(receita_total_milhoes_brl) AS registros_com_receita,
    CASE
      WHEN COUNT(*) = 20 AND COUNT(DISTINCT id_clube) = 20
      THEN 'OK' ELSE 'REVISAR'
    END AS validacao_estrutura
FROM workspace.pf1.vw_analise_clubes_2020_2025
GROUP BY ano
ORDER BY ano;

-- C. Duplicações indevidas (esperado: nenhuma linha)
SELECT id_clube, ano, COUNT(*) AS repeticoes
FROM workspace.pf1.vw_analise_clubes_2020_2025
GROUP BY id_clube, ano
HAVING COUNT(*) > 1
ORDER BY ano, id_clube;

-- D. Auditoria das chaves de origem que poderiam multiplicar os JOINs
-- Esperado: nenhuma linha; caso apareçam, verificar a tabela indicada.
SELECT 'clubes' AS tabela, CAST(id_clube AS STRING) AS chave, COUNT(*) AS repeticoes
FROM workspace.pf1.clubes GROUP BY id_clube HAVING COUNT(*) > 1
UNION ALL
SELECT 'clube_financeiro', CONCAT(CAST(id_clube AS STRING), ':', CAST(ano AS STRING)), COUNT(*)
FROM workspace.pf1.clube_financeiro GROUP BY id_clube, ano HAVING COUNT(*) > 1
UNION ALL
SELECT 'dados_financeiros', CAST(id_financeiro AS STRING), COUNT(*)
FROM workspace.pf1.dados_financeiros GROUP BY id_financeiro HAVING COUNT(*) > 1
UNION ALL
SELECT 'compras_e_vendas', CAST(id_financeiro AS STRING), COUNT(*)
FROM workspace.pf1.compras_e_vendas GROUP BY id_financeiro HAVING COUNT(*) > 1
UNION ALL
SELECT 'gastos_pessoal', CAST(id_financeiro AS STRING), COUNT(*)
FROM workspace.pf1.gastos_pessoal GROUP BY id_financeiro HAVING COUNT(*) > 1
UNION ALL
SELECT 'elencos', CONCAT(CAST(id_clube AS STRING), ':', CAST(ano AS STRING)), COUNT(*)
FROM workspace.pf1.elencos GROUP BY id_clube, ano HAVING COUNT(*) > 1
UNION ALL
SELECT 'saf', CONCAT(CAST(id_clube AS STRING), ':', CAST(ano AS STRING)), COUNT(*)
FROM workspace.pf1.saf GROUP BY id_clube, ano HAVING COUNT(*) > 1;
