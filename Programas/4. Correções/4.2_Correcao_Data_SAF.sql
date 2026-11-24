-- A. Conferência anterior à correção
SELECT id_clube, ano, virou_saf, data_entrada_saf, data_troca_controle
FROM workspace.pf1.saf
WHERE id_clube = 125
ORDER BY ano;

-- B. Atualizar somente os registros elegíveis e ainda sem data
UPDATE workspace.pf1.saf
SET data_entrada_saf = DATE '2022-01-05'
WHERE id_clube = 125
  AND ano IN (2022, 2023)
  AND virou_saf = TRUE
  AND data_entrada_saf IS NULL;

-- C. Conferência posterior à correção
SELECT id_clube, ano, virou_saf, data_entrada_saf, data_troca_controle
FROM workspace.pf1.saf
WHERE id_clube = 125
ORDER BY ano;
