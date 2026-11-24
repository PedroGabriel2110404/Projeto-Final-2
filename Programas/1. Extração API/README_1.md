# 01 — Extração de resultados pela API-Football

## Objetivo e quando utilizar

Esta pasta contém os códigos de obtenção dos resultados esportivos pela **API-Football**, para as temporadas **2022, 2023 e 2024**. As rotinas consultam a classificação do Campeonato Brasileiro e as campanhas dos clubes da Série A na Copa do Brasil e na Libertadores. **Sua Execução é opcional** e a reconstrução é necessária apenas para estudar ou repetir o pipeline esportivo. Quem utiliza o CSV consolidado `resultados_esportivos.csv` deve ir diretamente às pastas 05 e 06.

É necessário obter **sua própria chave** da API-Football. O documento `GUIA_CRIACAO_CHAVE_API_FOOTBALL.txt`, disponibilizado com os materiais de apoio, explica o cadastro, o teste e o tratamento da credencial.

## Chave de acesso

A API utiliza o cabeçalho HTTP `x-apisports-key`. **Não grave uma chave real em um arquivo enviado ao GitHub.** O mecanismo recomendado, quando disponível no ambiente, é um segredo do Databricks. Por exemplo:

A extração deve usar a variável de credencial esperada pelo próprio código. Não basta definir `API_KEY` em outro notebook se o arquivo executado procura, por exemplo, `API_FOOTBALL_KEY` em variável de ambiente. Confira a linha de autenticação do script e ajuste **somente sua configuração privada**.

Obs.: Os campos identificados como "Sua_Chave_API" devem ser substituídos pela chave gerada conforme o guia.

## Ordem prática

Deve-se criar uma célula e executar cada um dos programas a seguir, na ordem indicada:

1. **Verificação da API** após obter a chave, execute o programa que verifica seu funcionamento. Ele deve retornar 200 e as informações do usuário.
2. **Execute os arquivos de extração do Brasileirão** que consultam a classificação e constroem a base de posições e pontos de 2022–2024.
3. **Execute os arquivos de extração e tratamento das copas**. Os scripts classificam as fases alcançadas, selecionam os clubes da Série A e consolidam os resultados para as duas competições.
4. **Execute as etapas de persistência** do próprio pacote, garantindo que os DataFrames sejam salvos como tabelas Delta no schema ativo.
5. Confirme que as duas tabelas de saída estão acessíveis antes de passar à pasta 03.

> Atenção às versões: o arquivo de apoio `03_extracao_copas_corrigido.py` produz o **DataFrame Pandas `df_copas`**, mas **não grava sozinho** a tabela Delta `resultados_copas`. Caso utilize essa versão, também será necessária a rotina de armazenamento prevista no pipeline. Não misture versões alternativas sem verificar suas entradas e saídas.

## Saídas exigidas pela pasta 03

| Tabela | Conteúdo mínimo utilizado na integração |
|---|---|
| `resultados_brasileirao` | `id_api_clube`, `clube`, `ano`, `posicao_final`, `pontos` |
| `resultados_copas` | `id_api_clube`, `ano`, `competicao`, `fase_alcancada` |

Confira no SQL Editor:

```sql
SHOW TABLES IN workspace.pf1;

SELECT ano, COUNT(*) AS clubes
FROM workspace.pf1.resultados_brasileirao
GROUP BY ano ORDER BY ano;

SELECT ano, competicao, COUNT(*) AS campanhas
FROM workspace.pf1.resultados_copas
GROUP BY ano, competicao ORDER BY ano, competicao;
```

O Brasileirão deve apresentar **20 clubes por temporada** para 2022, 2023 e 2024. A quantidade de campanhas nas copas varia conforme a participação dos clubes.

## Problemas mais comuns

- **`403`, erro de credencial ou ausência de resposta:** examine os detalhes retornados pela API, os limites do plano e a autenticação.
- **`results: 0`:** verifique os filtros `league`, `season` e eventuais datas enviadas junto da consulta.
- **Fase não reconhecida:** inspecione o rótulo original retornado pela API; não substitua automaticamente por uma fase presumida.
- **Tabela ausente ao executar a pasta 03:** verifique se o resultado foi **gravado** como `resultados_brasileirao` e `resultados_copas`; um DataFrame exibido na tela não é necessariamente uma tabela persistida.