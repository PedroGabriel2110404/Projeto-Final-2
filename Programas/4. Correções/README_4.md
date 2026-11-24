# 04 — Correções e padronizações históricas

## Finalidade desta pasta

Esta pasta registra ajustes efetuados durante a construção e a revisão da base do projeto, como padronização de nomes de clubes, atualização pontual de registros das SAFs e alterações estruturais em tabelas.

> **Não é recomendado executar esta pasta sobre os oito CSVs consolidados.** As correções pertinentes já devem estar refletidas no material final. Os scripts servem, sobretudo, como documentação do processo e apoio à auditoria. Eles podem **alterar ou substituir dados**.

## Tipos de código documentados

| Código | O que fez |
|---|---|
| **4.1_Padronizacao_Nomes_Clubes** | Atualizou as nomenclaturas na tabela `clubes`, identificando cada equipe pelo `id_clube`. Os IDs não foram alterados. |
| **4.2_Correcao_Data_SAF** | Preencheu pontualmente a data de entrada na condição de SAF para registros que precisavam desse ajuste, respeitando os filtros de clube, temporada e valores nulos. |

**Exemplo de atualização histórica presente no material de desenvolvimento:** preenchimento condicionado de `data_entrada_saf` para o clube de ID 125, nos anos de 2022 e 2023, quando `virou_saf = TRUE` e a data está nula. Trata-se de um registro histórico da transformação, não de uma instrução para modificar os CSVs atuais.

## Verificações que podem ser feitas sem atualizar dados

```sql
SELECT id_clube, nome_clube
FROM workspace.pf1.clubes
ORDER BY id_clube;

SELECT id_clube, ano, virou_saf, tipo_controle,
       data_entrada_saf, data_troca_controle
FROM workspace.pf1.saf
ORDER BY id_clube, ano;

DESCRIBE TABLE workspace.pf1.resultados_esportivos;
```     