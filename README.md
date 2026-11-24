# Recursos Financeiros e Desempenho Esportivo no Futebol Brasileiro (2020–2025)

Este repositório reúne os scripts **Python/PySpark** e **SQL** utilizados no Projeto Final II para organizar dados financeiros e esportivos dos clubes da Série A, relacionar os resultados do Campeonato Brasileiro, da Copa do Brasil e da Libertadores e construir indicadores e datasets analíticos no **Databricks**.

O objetivo deste README é permitir que uma pessoa sem experiência prévia com o Databricks consiga **abrir a plataforma, carregar os dados, executar os códigos e consultar os resultados**.

> **Importante:** Para **reproduzir a base final e as análises**, é preciso importar os oito CSVs consolidados como tabelas no databricks, processo esse que será explicado no documento. Para quem quiser ver como foi o processo de **extração e o tratamento dos resultados esportivos**, execute o pipeline completo, sujeito à disponibilidade das fontes externas e da API-Football. As tabelas financeiras e complementares foram construídas manualmente.

## 1. Como o repositório está organizado

**Atenção:** As pastas de 1 a 3 servem apenas para quem quiser testar a extração dos dados.Enquanto a pasta 4 não é recomendado executá-la, pois é apenas uma padronização de algumas inconsistências identificadas nos dados.

Para a realização do projeto, é recomendado apenas o download dos arquivos .csv, e sua conversão para tabelas no schema, e o download das pastas 5 e 6.

O procedimento para utilizar cada arquivo das pastas será explicada em um README dentro de cada pasta.

```text
01 - Extração API/             # Resultados esportivos de 2022–2024
02 - Extração GitHub/          # Resultados esportivos de 2020, 2021 e 2025
03 - União API e GitHub/       # Consolidação dos seis anos
04 - Correções/                # Padronização dos clubes e dados SAF
05 - Criação da View/          # View analítica e validações
06 - SQL datasets/             # Consultas e indicadores do Apêndice E
README.md
```

| Etapa | Função | Principal resultado |
|---|---|---|
| 01 | Extrair Brasileirão e copas da API-Football | `resultados_brasileirao` e `resultados_copas` |
| 02 | Obter dados históricos de repositórios GitHub e consolidá-los | `stg_resultados_historicos_extra` |
| 03 | Reunir os dados esportivos das duas fontes e associar os IDs dos clubes | `resultados_esportivos` |
| 04 | Aplicar ajustes necessários nos cadastros e na SAF | Tabelas complementares ajustadas |
| 05 | Relacionar as oito tabelas do projeto | `vw_analise_clubes_2020_2025` |
| 06 | Executar análises financeiras, correlações, IDE e evolução SAF | Resultados de consultas SQL |

Todos os objetos finais devem estar no schema `workspace.pf1`, ou em um schema equivalente configurado pelo usuário.

## 2. Começando no Databricks

### 2.1. Criar uma conta e acessar a plataforma

1. Acesse o [Databricks Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition) e entre com uma conta existente ou crie uma conta informando o e-mail e criando uma senha.
2. Ao fazer o login, abra o **workspace**, que é o ambiente onde ficam os notebooks, arquivos, tabelas e consultas, localizada na terceira opção no canto esquerdo.

### 2.2. Criar um notebook e executar Python

1. No menu lateral, clique em **Create → Notebook** (ou crie um notebook dentro de **Workspace**).
2. No canto superior esquerdo do noteboook, selecione **Python** como linguagem.
3. No canto superior direito, ao lado de Run All, conecte-se ao servidor **Serverless**, caso a plataforma ainda não tenha se conectado automaticamente.
4. Ao preencher a célula com o código, execute a célula pelo botão de execução ou pelo atalho indicado no próprio editor.
5. Quando precisar de uma célula nova, clique nos três pontinhos no canto superior direito dela e escolha **Insert cell above** para inserir em cima, ou **Insert cell below** para inserir em baixo

### 2.3. Criar o schema do projeto

O projeto utiliza o catálogo `workspace` e o schema `pf1`. Para criá-los, crie uma célula e execute:

```sql
%sql
CREATE SCHEMA IF NOT EXISTS workspace.pf1;
SHOW TABLES IN workspace.pf1;
```

Para os scripts Python que usam nomes de tabela sem catálogo (por exemplo, `spark.table("resultados_brasileirao")`), selecione o contexto correto **na sessão em que cada script será executado**:

```python
spark.sql("USE CATALOG workspace")
spark.sql("USE SCHEMA pf1")
```
Ou em SQL apenas copie, cole e execute o código abaixo
```SQL
USE CATALOG workspace;
USE SCHEMA pf1;
```

## 3. Como utilizar os arquivos CSVs consolidados

### 3.1. Importar os oito arquivos CSV

No menu lateral esquerdo do Databricks, procure por **Catálogo**, clique em **workspace** e depois em **pf1**. Em seguida, clique em **Create** e depois em **Table**. Então selecione os arquivos CSV e faça o upload para o Databricks, um de cada vez.

**OBS:** Não é recomendado modificar os nomes das tabelas, pois eles são utilizados nos códigos SQL do projeto.

**Verifique na prévia antes de confirmar a importação:**

- Cabeçalho na primeira linha e separador de campos por vírgula (`CSV`).
- Identificadores e anos: inteiros (`INT`/`BIGINT`).
- Receitas, dívidas, valores de transferências e métricas de elenco: numéricos (`DOUBLE` ou `DECIMAL`).
- `virou_saf`: booleano (`BOOLEAN`).
- `data_entrada_saf` e `data_troca_controle`: datas (`DATE`).
- Valores escritos como `null` nos arquivos: precisam representar **NULL real**, especialmente em fases de copas e datas da SAF. Ajuste a configuração de importação ou converta-os após o upload.

A documentação oficial descreve o procedimento em [Criar ou modificar uma tabela por upload](https://docs.databricks.com/aws/pt/ingestion/create-or-modify-table).

### 3.2. Criar a view e usar os datasets

Com as oito tabelas disponíveis, siga os passos descritos nas pastas 5 e 6.

## 4. Problemas comuns

| Problema | O que verificar |
|---|---|
| `TABLE_OR_VIEW_NOT_FOUND` | Nome da tabela, catálogo/schema selecionado e execução das etapas anteriores |
| Falta de permissão para criar tabela/view | Permissões no catálogo e no schema de destino |
| Notebook sem executar | Recurso de computação conectado e cotas disponíveis |
| Erro de tipo em CSV | Tipos `INT`, `DOUBLE`/`DECIMAL`, `BOOLEAN`, `DATE` e conversão de `null` textual |
| Mais de 120 linhas na view | Chaves duplicadas em `clube_financeiro`, `elencos`, `saf` ou tabelas financeiras |
| Falha na API-Football | Credencial, plano, acesso à internet e limites da API |
| Resultado com fase ausente | Distinguir falta de participação de problemas na importação de `NULL` |

## 5. Fontes e documentação

**Fontes esportivas usadas no pipeline:**

- [API-Football](https://www.api-football.com/) — resultados da Série A, Copa do Brasil e Libertadores no intervalo tratado pela etapa 01.
- [guisomera/brasileirao-position-predictor](https://github.com/guisomera/brasileirao-position-predictor) — dados históricos do Brasileirão.
- [FerrerasRP/FootballData](https://github.com/FerrerasRP/FootballData) — dados históricos das copas.

**Documentação oficial do Databricks:**

- [Introdução à Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition)
- [Gerenciar notebooks](https://docs.databricks.com/aws/pt/notebooks/notebooks-manage)
- [Criar tabelas por upload de arquivos](https://docs.databricks.com/aws/pt/ingestion/create-or-modify-table)
- [Gerenciamento de segredos](https://docs.databricks.com/aws/pt/security/secrets)

---

**Escopo:** este README explica como utilizar o ambiente Databricks e executar o projeto. Ele não substitui o relatório acadêmico, o dicionário de dados, a documentação detalhada das tabelas manuais nem a verificação das fontes financeiras originais.
