# 05 — Criação e validação da view analítica

## Objetivo

A pasta 05 reúne as oito tabelas do projeto em uma **view analítica única**, com uma observação por **clube e temporada**. Essa view é a base das consultas e dos datasets da pasta 06. **Esta etapa é necessária** para reproduzir as análises a partir dos CSVs consolidados.

## Pré-requisitos

Importe os CSVs como tabelas Delta, usando exatamente estes nomes no schema `workspace.pf1`:

| Tabelas esportivas e cadastrais | Tabelas financeiras e complementares |
|---|---|
| `clubes` | `clube_financeiro` |
| `resultados_esportivos` | `dados_financeiros` |
| `elencos` | `gastos_pessoal` |
| `saf` | `compras_e_vendas` |

## Ordem de execução

1. Crie um **Notebook** e troque a linguagem padrão de **Python** para **SQL** e confirme o catálogo/schema `workspace.pf1` com o código:
```sql
USE CATALOG workspace;
USE SCHEMA pf1;
```
2. Faça a conferência inicial de que as **oito tabelas existem** e de que os seus campos foram importados com os tipos apropriados.
3. Execute o código presente em **5.1_Criacao_View_Analitica.sql** em outra célula. O comando deve criar ou substituir `workspace.pf1.vw_analise_clubes_2020_2025`.
4. Execute o arquivo de **5.2_Validacao_View.sql**. Se aparecer erro, corrija primeiro a tabela ou a referência indicada e somente depois repita a criação da view.

## Como o relacionamento funciona

A tabela `resultados_esportivos` fornece a chave `id_clube` + `ano`. A dimensão `clubes` adiciona o nome. A tabela `clube_financeiro` faz a ponte para `id_financeiro`, utilizado nos dados financeiros, gastos com pessoal e transferências. E as tabelas `elencos` e `saf` são vinculadas pelo par `id_clube` + `ano`.

As operações `LEFT JOIN` preservam os registros esportivos **quando não há correspondência** financeira. Entretanto, **chaves duplicadas podem multiplicar linhas** e precisam ser verificadas.

## Validação rápida (SQL Editor)

```sql
SELECT COUNT(*) AS total
FROM workspace.pf1.vw_analise_clubes_2020_2025;

SELECT ano,
       COUNT(*) AS linhas,
       COUNT(DISTINCT id_clube) AS clubes
FROM workspace.pf1.vw_analise_clubes_2020_2025
GROUP BY ano
ORDER BY ano;

SELECT COUNT(*) AS sem_vinculo_financeiro
FROM workspace.pf1.vw_analise_clubes_2020_2025
WHERE id_financeiro IS NULL;

SELECT *
FROM workspace.pf1.vw_analise_clubes_2020_2025
ORDER BY ano, nome_clube
LIMIT 20;
```

**Resultado esperado:** 120 linhas, com 20 clubes por ano de 2020 a 2025. O número de vínculos financeiros ausentes deve ser **analisado**, não presumido como zero.

## Problemas comuns

- **`TABLE_OR_VIEW_NOT_FOUND`:** importação ausente, nome errado, catálogo/schema diferente ou criação da view ainda não executada.
- **`UNRESOLVED_COLUMN`:** o SQL faz referência a uma coluna que não existe na versão importada. Preste atenção à remoção de `vitorias`, à permanência de `idade_media_elenco` e aos nomes dos campos financeiros.
- **Mais de 120 linhas:** verifique chaves únicas nas tabelas `clube_financeiro`, `elencos`, `saf` e nas tabelas ligadas por `id_financeiro`.
- **Colunas financeiras nulas:** verifique tipos dos identificadores e correspondências com `clube_financeiro`.
- **`CREATE OR REPLACE VIEW`:** substitui a definição anterior da view. Execute apenas no schema desejado.