# 02 — Extração histórica de resultados do GitHub

## Objetivo e quando utilizar

Esta pasta complementa a API-Football com dados de **2020, 2021 e 2025**. A extração usa os CSVs históricos do Brasileirão de `guisomera/brasileirao-position-predictor` e os JSONs de partidas das copas de `FerrerasRP/FootballData`. O processamento transforma os arquivos obtidos em campanhas por clube, ano e competição. **Sua execução é opcional** e a reconstrução é necessária apenas para estudar ou repetir o pipeline esportivo. Quem utiliza o CSV consolidado `resultados_esportivos.csv` deve ir diretamente às pastas 05 e 06.

Esta etapa **não usa** a chave da API-Football.

## Sequência de execução recomendada

Deve-se criar uma célula e executar cada um dos programas a seguir, na ordem indicada:

| Ordem | Código/atividade | Resultado esperado |
|---|---|---|
| 1 | `2.1_Extracao_Brasileirao.py` — extração dos resultados do Brasileirão histórico | `stg_brasileirao_historico_extra` |
| 2 | `2.2_Extracao_Tratamento_Copas.py` — extração e tratamento tanto da Copa do Brasil quanto da Libertadores | `stg_copa_do_brasil_historico_extra` e `stg_libertadores_historico_extra` |
| 3 | `2.3_Consolidacao_Resultados_GitHub.py` — união das três competições em uma base histórica | `stg_resultados_historicos_extra` |

**Atenção:** use os arquivos com esses nomes se estiverem presentes na sua pasta final. Caso a numeração do arquivo de consolidação tenha sido alterada no repositório, identifique-o pela saída `stg_resultados_historicos_extra`, não apenas pelo número.

## Conferência após a extração

```sql
SHOW TABLES IN workspace.pf1;

SELECT ano, competicao, COUNT(*) AS registros
FROM workspace.pf1.stg_resultados_historicos_extra
GROUP BY ano, competicao
ORDER BY ano, competicao;
```

A tabela histórica consolidada precisa fornecer à pasta 03 as colunas `clube`, `ano`, `competicao`, `posicao_final`, `pontos` e `fase_alcancada`. Os registros do Brasileirão, da Copa do Brasil e da Libertadores aparecem com seus respectivos valores em `competicao`.

## Pontos de atenção

1. O código identifica as **fases efetivamente alcançadas**, não presume a classificação do clube a partir de placares ausentes.
2. Na Libertadores, são mantidas as participações dos **clubes brasileiros**; a identificação depende da forma como a fonte registra seus nomes.
3. Os rótulos de fases preliminares da Libertadores e das primeiras fases da Copa do Brasil recebem tratamento específico, sobretudo para 2020.