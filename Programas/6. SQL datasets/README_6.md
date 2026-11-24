# 06 — Execução dos datasets analíticos (Apêndice E)

## Objetivo

Esta pasta contém as consultas SQL utilizadas para construir os **datasets das análises** do Projeto Final II: indicadores financeiros, correlações, comparações de desempenho, IDE (Índice de Desempenho Esportivo) e evolução das SAFs. **Esta etapa é recomendada** para quem importou os oito CSVs consolidados e já criou a view da pasta 05 e quer ver as visualizações dos dashboards.

## Pré-requisitos

1. As oito tabelas devem estar no schema `workspace.pf1` (ou em um schema equivalente ajustado nos scripts).
2. A view **`workspace.pf1.vw_analise_clubes_2020_2025`** deve existir e ter sido validada conforme a pasta 05.
Verificação inicial:

```sql
SELECT COUNT(*) AS registros
FROM workspace.pf1.vw_analise_clubes_2020_2025;
```

**Esperado:** 120 observações (20 clubes × 6 temporadas). Se a view ainda não existir ou tiver linhas duplicadas, resolva esse problema **antes** das análises.

## Como executar os arquivos da pasta

1. Vá ao menu lateral esquerdo e procure por **Dashboards**
2. Clique em **Create Dashboard** e no canto esquerdo clique em **Add Data**
3. Procure pela view **`vw_analise_clubes_2020_2025`** e clique em **Add**
4. Clique em **Add SQL dataset** e insira o código da consulta referente ao gráfico que queira montar

> **Não existe obrigação de executar todos os datasets em uma única sequência.** Depois de criada a view, a maioria das consultas é analisada individualmente. Entretanto, se um SQL criar uma view/tabela auxiliar usada por outro arquivo, execute primeiro essa definição conforme os comentários do próprio código.

## Tipos de datasets documentados no projeto

| Consulta | Função |
|---|---|
| 6.1_Relacao_Divida_Receita | Faz um cálculo de receita/divisão  |
| 6.2_Saldo_Transferencias | Faz um cálculo de compras - vendas |
| 6.3_Spearman_Brasileirao, 6.4_Spearman_Copa_do_Brasil e 6.5_Spearman_Libertadores | Verifica o quanto os indicadores foram influentes nas competições durante o ano |
| 6.6_Comparacao_Correlacoes | Ranking de qual fator financeiro foi mais eficiente|
| 6.7_IDE_Real_Indice_Financeiro_IDE_Esperado | Ponderação das competições, índice financeiro, previsão e diferença entre o resultado real e o esperado |
| 6.8_Evolucao_Esportiva_SAFs | Acompanha os resultados dos clubes que se tornaram SAF |

## Problemas comuns

- **`TABLE_OR_VIEW_NOT_FOUND`:** execute primeiro a pasta 05 e revise o caminho completo da view.
- **`UNRESOLVED_COLUMN`:** procure referências antigas a `vitorias`; a tabela consolidada não contém esse campo. `idade_media_elenco`, por outro lado, continua disponível no modelo final.
- **Erro de agregação ou função:** identifique o comando SQL específico e sua compatibilidade com a versão do Databricks.
- **Dataset vazio:** confira `WHERE`, valores nulos, anos e participação nas competições antes de concluir que faltam dados.
- **Resultado numérico divergente:** confirme que você não misturou consultas de diferentes versões do IDE, que os tipos de dados foram importados corretamente e que a view não multiplicou registros.