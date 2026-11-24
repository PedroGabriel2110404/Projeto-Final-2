# 03 — União dos resultados da API-Football e do GitHub

## Objetivo

Esta etapa reúne os dados esportivos da API-Football (**2022–2024**) e os registros históricos do GitHub (**2020, 2021 e 2025**). Também padroniza denominações, associa os identificadores dos clubes e cria a tabela final `resultados_esportivos`. **Sua execução é opcional** e a reconstrução é necessária apenas para estudar ou repetir o pipeline esportivo. Quem utiliza o CSV consolidado `resultados_esportivos.csv` deve ir diretamente às pastas 05 e 06

## Entradas e dependências

Os arquivos foram disponibilizados com os nomes abaixo:

| Arquivo | Tabelas que precisa encontrar |
|---|---|
| `3.1_Mescla_Resultados_API.py` | `resultados_brasileirao` e `resultados_copas` |
| `3.2_Uniao_API_GitHub.py` | `resultado_completo` (gerada por 3.1) e `stg_resultados_historicos_extra` (gerada na pasta 02) |

## Como executar

1. Crie um notebook Python ou abra `3.1_Mescla_Resultados_API.py` no Databricks. Conecte o processamento e execute o script inteiro. O código filtra os anos de 2022 a 2024, verifica colunas obrigatórias e duplicidades, faz `LEFT JOIN` das campanhas das copas ao Brasileirão e grava a tabela **`resultado_completo`**. Confirme que o resumo exibido apresenta **20 clubes em cada um dos três anos**, totalizando **60 linhas**.
2. Abra `3.2_Uniao_API_GitHub.py` em outra célula Python. Ele lê as tabelas **gravadas**, portanto não depende de variáveis temporárias deixadas pelo script 3.1. O código transforma as fases históricas em campos da campanha, normaliza nomes dos clubes e combina os seis anos. Em seguida, associa os IDs, verifica a ausência de valores nulos e duplicidades e grava **`resultados_esportivos`**.

## Conferir o resultado

```sql
SELECT ano,
       COUNT(*) AS registros,
       COUNT(DISTINCT id_clube) AS clubes_distintos
FROM workspace.pf1.resultados_esportivos
GROUP BY ano
ORDER BY ano;

SELECT COUNT(*) AS total_registros
FROM workspace.pf1.resultados_esportivos;
```

**Resultado esperado:** 120 linhas no total, sendo **20 clubes distintos por ano**, de 2020 a 2025. Os campos finais gravados por `3.2_Uniao_API_GitHub.py` são `id_clube`, `ano`, `posicao_final`, `pontos`, `fase_copa_brasil` e `fase_libertadores`.

O script **não grava** a coluna `clube` na tabela final: essa informação é utilizada apenas no processamento.

## Cuidados importantes

- **Substituição de tabela:** ambos os scripts utilizam gravação Delta em modo `overwrite`. Faça testes em outro schema se a tabela final já estiver importada e validada.
- **IDs:** o código utiliza IDs da API-Football e um complemento para clubes que não aparecem na amostra de 2022–2024. Se houver conflito entre IDs ou clube sem ID, a rotina interrompe a execução; não force IDs novos por suposição.
- **Nomes diferentes:** o processo faz normalização de acentos, abreviações e aliases. Se novos nomes forem introduzidos nas fontes, confira as mensagens de validação.
- **Fases das copas:** `NULL` pode significar ausência de participação; não trate todos os valores nulos como erro.
