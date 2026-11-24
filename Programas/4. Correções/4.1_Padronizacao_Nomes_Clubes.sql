WITH nomes_esperados AS (
  SELECT * FROM VALUES
    (125, 'America Mineiro'),
    (126, 'Sao Paulo'),
    (129, 'Ceara'),
    (130, 'Gremio'),
    (133, 'Vasco DA Gama'),
    (134, 'Atletico Paranaense'),
    (136, 'Vitoria'),
    (140, 'Criciuma'),
    (144, 'Atletico Goianiense'),
    (145, 'Avai'),
    (151, 'Goias'),
    (154, 'Fortaleza EC'),
    (794, 'RB Bragantino'),
    (1062, 'Atletico-MG'),
    (1193, 'Cuiaba')
  AS m(id_clube, nome_esperado)
)
SELECT
  e.id_clube,
  c.nome_clube AS nome_atual,
  e.nome_esperado,
  CASE
    WHEN c.id_clube IS NULL THEN 'ID NAO CADASTRADO'
    WHEN TRIM(c.nome_clube) = TRIM(e.nome_esperado) THEN 'SEM ALTERACAO'
    ELSE 'ATUALIZAR'
  END AS situacao
FROM nomes_esperados e
LEFT JOIN workspace.pf1.clubes c
  ON CAST(c.id_clube AS BIGINT) = CAST(e.id_clube AS BIGINT)
ORDER BY e.id_clube;

-- B. CORREÇÃO DOS NOMES CONFORME A LISTA DEFINIDA NO PF2
UPDATE workspace.pf1.clubes
SET nome_clube = CASE id_clube
    WHEN 125   THEN 'America Mineiro'
    WHEN 126   THEN 'Sao Paulo'
    WHEN 129   THEN 'Ceara'
    WHEN 130   THEN 'Gremio'
    WHEN 133   THEN 'Vasco DA Gama'
    WHEN 134   THEN 'Atletico Paranaense'
    WHEN 136   THEN 'Vitoria'
    WHEN 140   THEN 'Criciuma'
    WHEN 144   THEN 'Atletico Goianiense'
    WHEN 145   THEN 'Avai'
    WHEN 151   THEN 'Goias'
    WHEN 154   THEN 'Fortaleza EC'
    WHEN 794   THEN 'RB Bragantino'
    WHEN 1062  THEN 'Atletico-MG'
    WHEN 1193  THEN 'Cuiaba'
    ELSE nome_clube
END
WHERE id_clube IN (125, 126, 129, 130, 133, 134, 136, 140, 144, 145, 151, 154, 794, 1062, 1193);

-- C. CONFERÊNCIA APÓS A ATUALIZAÇÃO
SELECT id_clube, nome_clube
FROM workspace.pf1.clubes
WHERE id_clube IN (125, 126, 129, 130, 133, 134, 136, 140, 144, 145, 151, 154, 794, 1062, 1193)
ORDER BY id_clube;

-- Opcional: para comparar os nomes com aqueles obtidos em 2022–2024,
-- consulte a tabela intermediária 'resultado_completo' da etapa 3.1.
-- Não use 'resultados_esportivos.clube': essa coluna foi removida do esquema final.
-- Os clubes ausentes da extração da API não podem ser conferidos por essa via.
