# Projeto final do Módulo 1 do SCTEC.

## Qual o desafio?

Você participa de uma consultoria de dados que foi contratada pelo governo para dar mais transparência aos gastos públicos com viagens a serviço. O órgão responsável já publica os dados no Portal da Transparência, mas eles chegam brutos, desorganizados e a equipe precisa com urgência avaliar como anda o fluxo das informações das viagens. 

A sua missão é construir, do zero, um pipeline de dados que baixe essas informações, preservando o histórico original, limpar a estrutura e transformar os dados brutos em métricas e gráficos claros.

## Como foi resolvido?

Para encarar o desafio, foi usado SQL (MySQL), Python (com Pandas e Seaborn). Foi implementada a arquitetura medalhão, com o seguinte fluxo:

0_criar_banco.sql -> 1_extrair.py -> 2_transformar.py -> 3_analise.ipynb

## Estrutura do projeto

```text
PROJETO_MODULO_1 (WORKSPACE)
└── Projeto_Modulo_1
    ├── __pycache__
    │   ├── banco.cpython-313.pyc
    │   └── config.cpython-313.pyc
    ├── data
    │   └── viagens.zip
    ├── scripts
    │   ├── 1_extrair.py
    │   ├── 2_transformar.py
    │   └── 3_analise.ipynb
    ├── sql
    │   └── 0_criar_banco.sql
    ├── .env
    ├── .gitignore
    ├── banco.py
    ├── config.py
    ├── README.md
    └── requeriments.txt
```

## Como executar

Os arquivos devem ser executados nesta ordem:

0_criar_banco.sql -> 1_extrair.py -> 2_transformar.py -> 3_analise.ipynb

__Passo 01__

Execute __0_criar_banco.sql__ no banco de dados, para que o banco e as tabelas Raw e Silver sejam criadas.

__Passo 02__

Execute __1_extrair.py__ no terminal com o comando __python scripts/1_extrair.py__, para alimentar as tabelas Raw a partir dos dados de origem.

__Passo 03__

Execute __2_transformar.py__ no terminal com o comando __python scripts/2_transformar.py__, para alimentar as tabelas Silver a partir das tabelas Raw.

__Passo 04__

Execute as células de Jupyter Notebook do arquivo __3_analise.ipynb__ para obter os gráficos, tabelas e views da camada Gold.

## Conclusões e melhorias

Campos vazios comprometem a qualidade de certas análises. Prejudica, por exemplo, o cálculo de custo. Outro problema foi o enorme texto gerado para responder a pergunta sobre os destinos com maior custo médio. Especialmente no gráfico, o texto longo deixou a leitura bastante prejudicada.

Sei que não é o escopo deste projeto, todavia, tecnologias de automação, como Apache Airflow, serão muito úteis em projetos futuros. A organização dos gráficos em dashboard também será um próximo passo importante.