Recursos Financeiros e Desempenho Esportivo no Futebol Brasileiro (2020–2025)
Este repositório reúne os scripts Python/PySpark e SQL utilizados no Projeto Final II para organizar dados financeiros e esportivos dos clubes da Série A, relacionar os resultados do Campeonato Brasileiro, da Copa do Brasil e da Libertadores e construir indicadores e datasets analíticos no Databricks.

O objetivo deste README é permitir que uma pessoa sem experiência prévia com o Databricks consiga abrir a plataforma, carregar os dados, executar os códigos e consultar os resultados.
Importante: há duas maneiras de utilizar o projeto. Para reproduzir a base final e as análises, recomenda-se importar os oito CSVs consolidados (caminho A). Para reproduzir também a extração e o tratamento dos resultados esportivos, execute o pipeline completo (caminho B), sujeito à disponibilidade das fontes externas e da API-Football. As tabelas financeiras e complementares foram construídas manualmente e sua coleta será documentada separadamente.

1. Começando no Databricks
1.1. Criar uma conta e acessar o workspace
1. Acesse Databricks e entre com uma conta existente ou crie uma conta na Free Edition, se disponível para você.
2. Abra o workspace, que é o ambiente onde ficam os notebooks, arquivos, tabelas e consultas.
3. Localize as áreas principais na barra lateral (os nomes podem variar ligeiramente com a interface):
   - Workspace: organiza notebooks e arquivos de código.
   - Catalog / Catalog Explorer: mostra catálogos, schemas, tabelas e views.
   - SQL Editor: executa as consultas .sql e permite explorar os resultados.
   - Compute: disponibiliza os recursos de processamento, conforme as permissões e o plano.
A Free Edition utiliza computação serverless e possui cotas de uso. A disponibilidade de opções de computação pode variar entre contas.
1.2. Criar um notebook e executar Python
1. No menu lateral, clique em New → Notebook (ou crie um notebook dentro de Workspace).
2. Selecione Python como linguagem e conecte um recurso de computação, caso a plataforma ainda não tenha conectado automaticamente.
3. Em uma célula de Python, experimente:
print("Databricks funcionando!")
display(spark.range(5))
4. Execute a célula pelo botão de execução ou pelo atalho indicado no próprio editor.
O objeto spark já está disponível nos notebooks Databricks com Spark. Para executar SQL dentro de um notebook Python, é possível usar uma célula %sql ou spark.sql(...).
1.3. Criar o schema do projeto
O projeto utiliza o catálogo workspace e o schema pf1. No SQL Editor, execute:
CREATE SCHEMA IF NOT EXISTS workspace.pf1;
SHOW TABLES IN workspace.pf1;
O catálogo workspace não é universal: ele precisa existir na sua conta e você deve ter permissão para criar o schema. Se o seu workspace oferecer outro catálogo, substitua workspace de forma consistente nas consultas e nos scripts.

Para os scripts Python que usam nomes de tabela sem catálogo (por exemplo, spark.table("resultados_brasileirao")), selecione o contexto correto na sessão em que cada script será executado:
spark.sql("USE CATALOG workspace")
spark.sql("USE SCHEMA pf1")
No SQL Editor, também é possível selecionar o catálogo e o schema pelo próprio cabeçalho da consulta. Consulte a documentação do SQL Editor.
2. Como o repositório está organizado
01 - Extração API/             # Resultados esportivos de 2022–2024
02 - Extração GitHub/          # Resultados esportivos de 2020, 2021 e 2025
03 - União API e GitHub/       # Consolidação dos seis anos
04 - Correções/                # Padronização dos clubes e dados SAF
05 - Criação da View/          # View analítica e validações
06 - SQL datasets/             # Consultas e indicadores do Apêndice E
README.md
Etapa	Função	Principal resultado
01	Extrair Brasileirão e copas da API-Football	resultados_brasileirao e resultados_copas
02	Obter dados históricos de repositórios GitHub e consolidá-los	stg_resultados_historicos_extra
03	Reunir os dados esportivos das duas fontes e associar os IDs dos clubes	resultados_esportivos
04	Aplicar ajustes necessários nos cadastros e na SAF	Tabelas complementares ajustadas
05	Relacionar as oito tabelas do projeto	vw_analise_clubes_2020_2025
06	Executar análises financeiras, correlações, IDE e evolução SAF	Resultados de consultas SQL


Todos os objetos finais devem estar no schema workspace.pf1, ou em um schema equivalente configurado pelo usuário.
3. Caminho A — Reproduzir as análises usando os CSVs consolidados
Recomendado para quem deseja executar as análises sem depender da API-Football. Esse caminho utiliza os arquivos já consolidados como ponto de partida, sem repetir a extração dos resultados esportivos.
3.1. Importar os oito arquivos CSV
No Databricks, abra New → Add or upload data → Create or modify a table. Selecione um arquivo CSV, escolha o catálogo e o schema workspace.pf1, confira o cabeçalho e os tipos e crie a tabela. Repita para os demais arquivos. A interface permite criar tabelas Delta diretamente a partir do upload de arquivos locais.

Utilize estes nomes de tabela:
Arquivo fornecido	Nome da tabela
clubes.csv	clubes
resultados_esportivos.csv	resultados_esportivos_importado (temporária; veja 3.2)
elencos(1).csv	elencos
saf(4).csv	saf
clube_financeiro(1).csv	clube_financeiro
dados_financeiros(3).csv	dados_financeiros
gastos_pessoal(1).csv	gastos_pessoal
compras_e_vendas(1).csv	compras_e_vendas


Os sufixos (1), (3) e (4) são apenas parte dos nomes dos arquivos exportados; não fazem parte dos nomes das tabelas. Se os CSVs forem renomeados para nomes mais simples, mantenha a correspondência indicada acima.

Verifique na prévia antes de confirmar a importação:
- Cabeçalho na primeira linha e separador de campos por vírgula (CSV).
- Identificadores e anos: inteiros (INT/`BIGINT`).
- Receitas, dívidas, valores de transferências e métricas de elenco: numéricos (DOUBLE ou DECIMAL).
- virou_saf: booleano (BOOLEAN).
- data_entrada_saf e data_troca_controle: datas (DATE).
- Valores escritos como null nos arquivos: precisam representar NULL real, especialmente em fases de copas e datas da SAF. Ajuste a configuração de importação ou converta-os após o upload.
A documentação oficial descreve o procedimento em Criar ou modificar uma tabela por upload.
3.2. Criar a tabela esportiva com o esquema definitivo
O CSV exportado de resultados_esportivos possui a coluna histórica vitorias. Ela não faz parte do esquema final. Por isso, a tabela é inicialmente importada com o nome resultados_esportivos_importado e depois convertida em uma tabela definitiva sem vitorias, sem clube e sem origem_dados:
CREATE OR REPLACE TABLE workspace.pf1.resultados_esportivos
USING DELTA AS
SELECT
    CAST(id_clube AS INT) AS id_clube,
    CAST(ano AS INT) AS ano,
    CAST(posicao_final AS INT) AS posicao_final,
    CAST(pontos AS INT) AS pontos,
    NULLIF(TRIM(fase_copa_brasil), 'null') AS fase_copa_brasil,
    NULLIF(TRIM(fase_libertadores), 'null') AS fase_libertadores
FROM workspace.pf1.resultados_esportivos_importado;
Esse comando cria a tabela final sem alterar ou apagar o CSV de origem. Ele pressupõe que as seis colunas selecionadas tenham sido importadas com seus nomes corretos.
3.3. Conferir as tabelas
SHOW TABLES IN workspace.pf1;

SELECT ano, COUNT(*) AS clubes
FROM workspace.pf1.resultados_esportivos
GROUP BY ano
ORDER BY ano;
Resultado esperado: 120 registros esportivos, distribuídos em 20 clubes por ano, de 2020 a 2025. As demais tabelas complementares possuem dados associados a essas temporadas; consulte a seção 5 para validar os relacionamentos.
3.4. Criar a view e usar os datasets
Com as oito tabelas disponíveis:
1. Execute 05 - Criação da View/5.1_Criacao_View_Analitica.sql.
2. Execute 05 - Criação da View/5.2_Validacao_View.sql.
3. Abra os arquivos da pasta 06 - SQL datasets no SQL Editor e execute as consultas desejadas.
As atualizações da pasta 04 já podem estar refletidas nos CSVs disponibilizados. Não é necessário aplicá-las novamente apenas para importar a versão consolidada; utilize-as como referência de transformação e auditoria.
4. Caminho B — Reconstruir os resultados esportivos desde as fontes
Esse caminho serve para estudar e reproduzir o pipeline de extração e transformação. Antes de começar, importe as sete tabelas complementares (clubes, elencos, saf, clube_financeiro, dados_financeiros, gastos_pessoal, compras_e_vendas). Neste caminho, resultados_esportivos será gerada pelos scripts da etapa 03, não importada do CSV.
4.1. Preparar os scripts
1. Crie notebooks Python ou adicione os arquivos .py ao workspace, de acordo com as opções disponíveis na interface.
2. Configure a sessão para o catálogo e schema do projeto (USE CATALOG workspace, USE SCHEMA pf1), pois alguns scripts usam nomes de tabela sem qualificação.
3. Garanta acesso aos pacotes Python utilizados. Spark/PySpark está disponível no ambiente Databricks; requests e pandas podem precisar estar disponíveis na sessão.
4. Para scripts da API-Football, obtenha uma chave válida e não a publique no repositório. Prefira recursos de gerenciamento de segredos do Databricks, se disponíveis.
Exemplo de leitura de um segredo em notebook Python (ajuste o script de extração para usar a variável correspondente):
API_KEY = dbutils.secrets.get(scope="pf2", key="api-football-key")
O exemplo acima só funcionará após a criação e a configuração do escopo/segredo pf2; ele não cria nem configura o segredo automaticamente.
4.2. Ordem de execução
Ordem	Arquivo ou etapa	Dependência
1	01 - Extração API (extrações do Brasileirão e das copas)	Chave API-Football ativa e acesso externo
2	02 - Extração GitHub/2.1_Extracao_Brasileirao.py	Acesso aos CSVs históricos do GitHub
3	02 - Extração GitHub/2.2_Extracao_Tratamento_Copas.py	Acesso aos JSONs históricos do GitHub
4	02 - Extração GitHub/2.3_Consolidacao_Resultados_GitHub.py	Tabelas geradas por 2.1 e 2.2
5	03 - União API e GitHub/3.1_Mescla_Resultados_API.py	Tabelas da etapa 01
6	03 - União API e GitHub/3.2_Uniao_API_GitHub.py	Saídas 2.3 e 3.1
7	04 - Correções	Tabelas complementares já criadas
8	05 - Criação da View	Todas as oito tabelas finais
9	06 - SQL datasets	View consolidada disponível


Os dados da API-Football abrangem 2022, 2023 e 2024. A parte histórica do GitHub cobre 2020, 2021 e 2025, com as fontes guisomera/brasileirao-position-predictor (Brasileirão) e FerrerasRP/FootballData (copas).
Limitação: a extração completa não foi validada em um workspace Databricks novo. O acesso à API-Football pode estar indisponível, suspenso ou sujeito a cotas. Se isso acontecer, o caminho A continua permitindo consultar o banco consolidado.

4.3. Evitar sobrescrever resultados acidentalmente
Alguns scripts utilizam mode("overwrite") ou CREATE OR REPLACE. Isso substitui tabelas existentes. Execute em um schema de teste antes de usar sobre tabelas já preenchidas ou ajustadas manualmente.
5. Consultar os resultados e validar a integração
No SQL Editor ou em uma célula %sql de notebook, execute:
-- Verificar o volume de registros na view final
SELECT COUNT(*) AS total
FROM workspace.pf1.vw_analise_clubes_2020_2025;

-- Verificar a quantidade de clubes em cada temporada
SELECT
    ano,
    COUNT(*) AS registros,
    COUNT(DISTINCT id_clube) AS clubes_distintos
FROM workspace.pf1.vw_analise_clubes_2020_2025
GROUP BY ano
ORDER BY ano;

-- Explorar as primeiras linhas
SELECT *
FROM workspace.pf1.vw_analise_clubes_2020_2025
ORDER BY ano, nome_clube
LIMIT 20;
O resultado esperado é uma view com 120 linhas, sendo 20 clubes distintos em cada uma das seis temporadas. Se houver mais de 120 linhas, revise os identificadores e as chaves das tabelas associadas: um LEFT JOIN não evita multiplicações causadas por duplicidades.

A view relaciona oito tabelas: clubes, resultados_esportivos, elencos, saf, clube_financeiro, dados_financeiros, gastos_pessoal e compras_e_vendas. O campo idade_media_elenco permanece no modelo, assim como valor_elenco_milhoes_eur.

Para criar gráficos, execute uma consulta no SQL Editor e utilize os controles de visualização disponíveis para o resultado. As consultas da pasta 06 incluem:
- relação dívida/receita e saldo de transferências;
- correlações de Spearman nas três competições e comparação de indicadores;
- IDE Real, Índice Financeiro, IDE Esperado e erro MAE;
- evolução do desempenho esportivo das SAFs.
As consultas da pasta 06 reproduzem as consultas documentadas no Apêndice E e podem ter requisitos específicos de compatibilidade com a versão do Databricks utilizada.
6. Problemas comuns
Problema	O que verificar
TABLE_OR_VIEW_NOT_FOUND	Nome da tabela, catálogo/schema selecionado e execução das etapas anteriores
Falta de permissão para criar tabela/view	Permissões no catálogo e no schema de destino
Notebook sem executar	Recurso de computação conectado e cotas disponíveis
Erro de tipo em CSV	Tipos INT, DOUBLE/`DECIMAL`, BOOLEAN, DATE e conversão de null textual
Mais de 120 linhas na view	Chaves duplicadas em clube_financeiro, elencos, saf ou tabelas financeiras
Falha na API-Football	Credencial, plano, acesso à internet e limites da API; alternativamente, usar o caminho A
Resultado com fase ausente	Distinguir falta de participação de problemas na importação de NULL


7. Fontes e documentação
Fontes esportivas usadas no pipeline:
- API-Football — resultados da Série A, Copa do Brasil e Libertadores no intervalo tratado pela etapa 01.
- guisomera/brasileirao-position-predictor — dados históricos do Brasileirão.
- FerrerasRP/FootballData — dados históricos das copas.
Documentação oficial do Databricks:
- Introdução à Free Edition
- Gerenciar notebooks
- Criar tabelas por upload de arquivos
- Editor SQL
- Gerenciamento de segredos
Escopo: este README explica como utilizar o ambiente Databricks e executar o projeto. Ele não substitui o relatório acadêmico, o dicionário de dados, a documentação detalhada das tabelas manuais nem a verificação das fontes financeiras originais.
