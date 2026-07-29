import sys
from pathlib import Path

import mysql.connector

# Adiciona a pasta raiz (Projeto_Modulo_1) ao caminho do Python
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import gdown

import config
import banco

# -------------------------------------------------------------------------
# Passo 1 - Baixar o arquivo .zip do Google Drive

def baixar_zip():
    print("Iniciando script...")
    """Baixa o .zip do Drive (so se ele ainda nao estiver na pasta data/)."""
    config.PASTA_DADOS.mkdir(exist_ok=True)
    destino = config.PASTA_DADOS / "viagens.zip"

    if destino.exists():
        print("[1/3] O arquivo ja foi baixado antes - pulando o download.")
    else:
        print("[1/3] Baixando o arquivo do Google Drive...")
        gdown.download(id=config.DRIVE_FILE_ID, output=str(destino))
    return destino

// Para execução via terminal
if __name__ == "__main__":
    caminho_zip = baixar_zip()

--------------------------------------------------------------------------
# Passo 2 - Extrair os CSVs do zip e carregar no MySQL

def carregar_csv(conexao, zip_aberto, nome_csv, tabela):
    """Le um CSV de dentro do zip e insere todas as linhas na tabela do MySQL.

    As colunas do CSV estao na MESMA ordem das colunas da tabela
    (definidas no 0_criar_banco.sql). Por isso conseguimos inserir "na ordem",
    sem precisar escrever o nome de cada coluna.
    """
    print("    Carregando", tabela, "...")

    # esvazia a tabela antes de carregar (assim, rodar de novo nao duplica dados)
    banco.executar(conexao, f"TRUNCATE TABLE {tabela}")

    total = 0
    with zip_aberto.open(nome_csv) as arquivo:
        # le o CSV em pedacos de 50 mil linhas, para nao encher a memoria do PC
        pedacos = pd.read_csv(
            arquivo,
            sep=";",                  # as colunas sao separadas por ponto-e-virgula
            encoding="latin-1",       # acentuacao dos arquivos do governo
            dtype=str,                # tudo como texto (camada RAW)
            keep_default_na=False,    # campo vazio continua "" (nao vira "NaN")
            chunksize=config.TAMANHO_BLOCO,
        )
        for pedaco in pedacos: