import sys
from pathlib import Path

# Adiciona a pasta raiz (Projeto_Modulo_1) ao caminho do Python
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import banco

# -------------------------------------------------------------------------
# Funções de tratamento de dados

def importar_raw(conexao, tabela):
    """Extrai os dados da camada Raw e converte para DataFrame com Pandas."""
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {tabela}")
    linhas = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(linhas)

def truncar_tabelas(conexao):
    """Garante que as tabelas Silver estejam vazias antes da carga."""
    print("[1/5] Limpando tabelas Silver (TRUNCATE)...")
    banco.executar(conexao, "SET FOREIGN_KEY_CHECKS = 0;")
    
    banco.executar(conexao, "TRUNCATE TABLE silver_pagamento;")
    banco.executar(conexao, "TRUNCATE TABLE silver_passagem;")
    banco.executar(conexao, "TRUNCATE TABLE silver_trecho;")
    banco.executar(conexao, "TRUNCATE TABLE silver_viagem;")
    
    banco.executar(conexao, "SET FOREIGN_KEY_CHECKS = 1;")

def limpar_moeda(serie):
    """Substituir vírgula por ponto."""
    serie = serie.astype(str).str.strip()
    serie = serie.replace(['', 'nan', 'None'], '0')
    serie = serie.str.replace('.', '', regex=False)  # Remove ponto de milhar
    serie = serie.str.replace(',', '.', regex=False) # Troca vírgula por ponto
    return pd.to_numeric(serie, errors='coerce').fillna(0.0)

def limpar_data(serie):
    """Converte data no formato dd/mm/yyyy para YYYY-MM-DD."""
    dt = pd.to_datetime(serie, dayfirst=True, errors='coerce')
    return dt

def padronizar_nulos(df):
    """Substitui campos vazios, NaN ou NaT por Null."""
    df = df.replace({"": None, "nan": None, "None": None, np.nan: None})
    return df

def inserir_em_blocos(conexao, sql, linhas, tamanho_lote=5000):
    """Divide a inserção em pedaços menores para evitar erro de limite do MySQL."""
    for i in range(0, len(linhas), tamanho_lote):
        lote = linhas[i : i + tamanho_lote]
        banco.inserir_em_lote(conexao, sql, lote)

# -------------------------------------------------------------------------
# Transformação das colunas

def transformar_viagens(conexao):
    print("[2/5] Transformando raw_viagem -> silver_viagem...")
    df = importar_raw(conexao, "raw_viagem")
    if df.empty:
        return set()

    data_ini_dt = limpar_data(df['data_inicio'])
    data_fim_dt = limpar_data(df['data_fim'])
    
    df['data_inicio'] = data_ini_dt.dt.strftime('%Y-%m-%d')
    df['data_fim'] = data_fim_dt.dt.strftime('%Y-%m-%d')
    
    df['duracao_dias'] = (data_fim_dt - data_ini_dt).dt.days

    colunas_moeda = ['valor_diarias', 'valor_passagens', 'valor_devolucao', 'valor_outros_gastos']
    for col in colunas_moeda:
        df[col] = limpar_moeda(df[col])

    df['valor_total'] = df[colunas_moeda].sum(axis=1)
    
    df = df.drop_duplicates(subset=['id_viagem'])
    
    df['nome_orgao_superior'] = df['nome_orgao_superior'].fillna("Não Informado")
    df = padronizar_nulos(df)
    
    colunas_silver = [
        'id_viagem', 'num_proposta', 'situacao', 'viagem_urgente', 'cod_orgao_superior', 
        'nome_orgao_superior', 'nome_viajante', 'cargo', 'data_inicio', 'data_fim', 
        'destinos', 'motivo', 'valor_diarias', 'valor_passagens', 'valor_devolucao', 
        'valor_outros_gastos', 'valor_total', 'duracao_dias'
    ]
    df_silver = df[colunas_silver]
    
    linhas = [tuple(x) for x in df_silver.to_numpy()]
    sql = f"INSERT INTO silver_viagem ({', '.join(colunas_silver)}) VALUES ({', '.join(['%s'] * len(colunas_silver))})"
    
    inserir_em_blocos(conexao, sql, linhas)
    
    return set(df_silver['id_viagem'].dropna())


def transformar_pagamentos(conexao, ids_validos):
    print("[3/5] Transformando raw_pagamento -> silver_pagamento...")
    df = importar_raw(conexao, "raw_pagamento")
    if df.empty: return

    df = df[df['id_viagem'].isin(ids_validos)]

    df['valor'] = limpar_moeda(df['valor'])
    df['tipo_pagamento'] = df['tipo_pagamento'].fillna("Não Informado")
    
    df = padronizar_nulos(df)
    
    colunas_silver = ['id_viagem', 'num_proposta', 'nome_orgao_pagador', 'nome_ug_pagadora', 'tipo_pagamento', 'valor']
    linhas = [tuple(x) for x in df[colunas_silver].to_numpy()]
    sql = f"INSERT INTO silver_pagamento ({', '.join(colunas_silver)}) VALUES ({', '.join(['%s'] * len(colunas_silver))})"
    
    inserir_em_blocos(conexao, sql, linhas)


def transformar_passagens(conexao, ids_validos):
    print("[4/5] Transformando raw_passagem -> silver_passagem...")
    df = importar_raw(conexao, "raw_passagem")
    if df.empty: return

    df = df[df['id_viagem'].isin(ids_validos)]

    df['valor_passagem'] = limpar_moeda(df['valor_passagem'])
    df['taxa_servico'] = limpar_moeda(df['taxa_servico'])
    df['data_emissao'] = limpar_data(df['data_emissao']).dt.strftime('%Y-%m-%d')
    
    df = padronizar_nulos(df)
    
    colunas_silver = [
        'id_viagem', 'meio_transporte', 'pais_origem_ida', 'uf_origem_ida', 'cidade_origem_ida', 
        'pais_destino_ida', 'uf_destino_ida', 'cidade_destino_ida', 'valor_passagem', 'taxa_servico', 'data_emissao'
    ]
    linhas = [tuple(x) for x in df[colunas_silver].to_numpy()]
    sql = f"INSERT INTO silver_passagem ({', '.join(colunas_silver)}) VALUES ({', '.join(['%s'] * len(colunas_silver))})"
    
    inserir_em_blocos(conexao, sql, linhas)


def transformar_trechos(conexao, ids_validos):
    print("[5/5] Transformando raw_trecho -> silver_trecho...")
    df = importar_raw(conexao, "raw_trecho")
    if df.empty: return

    df = df[df['id_viagem'].isin(ids_validos)]

    df['origem_data'] = limpar_data(df['origem_data']).dt.strftime('%Y-%m-%d')
    df['destino_data'] = limpar_data(df['destino_data']).dt.strftime('%Y-%m-%d')
    df['numero_diarias'] = limpar_moeda(df['numero_diarias'])
    df['sequencia_trecho'] = pd.to_numeric(df['sequencia_trecho'], errors='coerce')
    
    df = df.drop_duplicates(subset=['id_viagem', 'sequencia_trecho'])
    
    df = padronizar_nulos(df)
    
    colunas_silver = [
        'id_viagem', 'sequencia_trecho', 'origem_data', 'origem_uf', 'origem_cidade', 
        'destino_data', 'destino_uf', 'destino_cidade', 'meio_transporte', 'numero_diarias'
    ]
    linhas = [tuple(x) for x in df[colunas_silver].to_numpy()]
    sql = f"INSERT INTO silver_trecho ({', '.join(colunas_silver)}) VALUES ({', '.join(['%s'] * len(colunas_silver))})"
    
    inserir_em_blocos(conexao, sql, linhas)


# -------------------------------------------------------------------------
# Main da Fase 2 - Transformação e Carga na Camada Silver

def main():
    print("=== FASE 2: TRANSFORMACAO + CAMADA SILVER ===")
    conexao = banco.conectar()
    
    try:
        truncar_tabelas(conexao)
        
        ids_viagens_validas = transformar_viagens(conexao)
        
        transformar_pagamentos(conexao, ids_viagens_validas)
        transformar_passagens(conexao, ids_viagens_validas)
        transformar_trechos(conexao, ids_viagens_validas)
        
        print("=== Transformação concluída com sucesso! ===")
        
    except Exception as erro:
        print("[ERRO] Falha durante a transformação na Camada Silver:", erro)
        raise
    finally:
        conexao.close()

if __name__ == "__main__":
    main()