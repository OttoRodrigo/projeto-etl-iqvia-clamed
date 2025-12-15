from database import connect_db
import pandas as pd
import psycopg2
from typing import Dict
from datetime import datetime

def load_filiais(
    df_filiais: pd.DataFrame,
    db_config: Dict[str, str],
    modo: str = 'upsert'
) -> Dict[str, any]:
    """
    Carrega dados de filiais já transformados para tabela dim_brick_filial.
    """
    
    stats = {
        'tabela': 'dim_brick_filial',
        'total_processados': len(df_filiais),
        'registros_validos': 0,
        'inseridos': 0,
        'ignorados': 0,
        'erros': [],
        'inicio': datetime.now(),
        'fim': None,
        'duracao': None
    }
    
    colunas_necessarias = ['COD_BRICK', 'COD_FILIAL', 'NOME_BRICK']
    colunas_faltantes = [col for col in colunas_necessarias if col not in df_filiais.columns]
    
    if colunas_faltantes:
        stats['erros'].append(f"Colunas faltantes: {colunas_faltantes}")
        print(f" Erro: DataFrame não tem colunas necessárias")
        print(f"   Colunas atuais: {list(df_filiais.columns)}")
        return stats
    
    conn = None
    cursor = None
    
    try:
        conn = connect_db(**db_config)
        cursor = conn.cursor()
        
        print(f"📤 LOAD FILIAIS - Conectado ao banco")
        print(f"   Registros para carregar: {len(df_filiais)}")
        
        df_validos = df_filiais[
            (df_filiais['COD_BRICK'] > 0) &
            (df_filiais['COD_FILIAL'] > 0) &
            (df_filiais['NOME_BRICK'].notna())
        ].drop_duplicates(subset=['COD_BRICK', 'COD_FILIAL'])
        
        stats['registros_validos'] = len(df_validos)
        
        if df_validos.empty:
            print(" Nenhum registro válido para carregar")
            return stats
        
        print(f"   Registros válidos: {len(df_validos)}")
        
        if modo == 'upsert':
            query = """
            INSERT INTO dim_brick_filial (cod_brick, cod_filial, nome_brick)
            VALUES (%s, %s, %s)
            ON CONFLICT (cod_brick, cod_filial) DO NOTHING;
            """ 
        else:
            query = """
            INSERT INTO dim_brick_filial (cod_brick, cod_filial, nome_brick)
            VALUES (%s, %s, %s);
            """ 
        
        dados = []
        for _, row in df_validos.iterrows():
            try:
                registro = (
                    int(row['COD_BRICK']),
                    int(row['COD_FILIAL']),
                    str(row['NOME_BRICK'])[:255]
                )
                dados.append(registro)
            except Exception as e:
                stats['erros'].append(f"Erro ao processar linha: {e}")
                continue
        
        print(f"   Dados preparados: {len(dados)} registros")
        
        inseridos = 0
        batch_size = 1000
        
        for i in range(0, len(dados), batch_size):
            batch = dados[i:i + batch_size]
            
            try:
                cursor.executemany(query, batch)
                inseridos += cursor.rowcount
                
                progresso = min(i + batch_size, len(dados))
                print(f"   Progresso: {progresso}/{len(dados)} registros", end='\r')
                
            except psycopg2.Error as e:
                conn.rollback()
                stats['erros'].append(f"Erro no lote {i//batch_size}: {e}")
                print(f"\n Erro no lote: {e}")
                continue
        
        print(f"\n   Registros inseridos: {inseridos}")
        
        conn.commit()
        stats['inseridos'] = inseridos
        stats['ignorados'] = len(dados) - inseridos
        
    except Exception as e:
        if conn:
            conn.rollback()
        stats['erros'].append(f"Erro geral: {e}")
        print(f" Erro no load_filiais: {e}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        
        stats['fim'] = datetime.now()
        stats['duracao'] = (stats['fim'] - stats['inicio']).total_seconds()
        
        print(f" LOAD FILIAIS finalizado em {stats['duracao']:.2f}s")
        print(f"   Inseridos: {stats['inseridos']}")
        print(f"   Ignorados: {stats['ignorados']}")
    
    return stats

def load_iqvia(
    df_iqvia: pd.DataFrame,
    db_config: Dict[str, str],
    modo: str = 'upsert'
) -> Dict[str, any]:
    """
    Carrega dados IQVIA já transformados para tabela fact_iqvia.
    """
    
    stats = {
        'tabela': 'fact_iqvia',
        'total_processados': len(df_iqvia),
        'registros_validos': 0,
        'inseridos': 0,
        'erros': [],
        'inicio': datetime.now(),
        'fim': None,
        'duracao': None
    }
    
    colunas_essenciais = ['COD_BRICK', 'EAN', 'COD_PRODUTO']
    colunas_faltantes = [col for col in colunas_essenciais if col not in df_iqvia.columns]
    
    if colunas_faltantes:
        stats['erros'].append(f"Colunas faltantes: {colunas_faltantes}")
        print(f" Erro: DataFrame não tem colunas essenciais")
        print(f"   Colunas atuais: {list(df_iqvia.columns)}")
        return stats
    
    colunas_numericas = ['CONCORRENTE_SI', 'CONCORRENTE_SO', 'PRECO_POPULAR', 
                         'VOL_TOTAL_MERCADO', 'PARTICIPACAO_CLAMED']
    
    for col in colunas_numericas:
        if col not in df_iqvia.columns:
            df_iqvia[col] = 0.0
            print(f" Coluna {col} não encontrada, criando com valor 0")
    
    conn = None
    cursor = None
    
    try:
        conn = connect_db(**db_config)
        cursor = conn.cursor()
        
        print(f"📤 LOAD IQVIA - Conectado ao banco")
        print(f"   Registros para carregar: {len(df_iqvia)}")
        
        df_validos = df_iqvia[
            (df_iqvia['COD_BRICK'] > 0) &
            (df_iqvia['EAN'].notna()) &
            (df_iqvia['COD_PRODUTO'].notna())
        ].copy()
        
        stats['registros_validos'] = len(df_validos)
        
        if df_validos.empty:
            print(" Nenhum registro válido para carregar")
            return stats
        
        print(f"   Registros válidos: {len(df_validos)}")
        
        if modo == 'upsert':
            query = """
            INSERT INTO fact_iqvia (
                cod_brick, ean, cod_produto, 
                concorrente_si, concorrente_so, preco_popular,
                vol_total_mercado, participacao_clamed
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cod_brick, ean, cod_produto) 
            DO UPDATE SET
                concorrente_si = EXCLUDED.concorrente_si,
                concorrente_so = EXCLUDED.concorrente_so,
                preco_popular = EXCLUDED.preco_popular,
                vol_total_mercado = EXCLUDED.vol_total_mercado,
                participacao_clamed = EXCLUDED.participacao_clamed;
            """  
        else:
            query = """
            INSERT INTO fact_iqvia (
                cod_brick, ean, cod_produto, 
                concorrente_si, concorrente_so, preco_popular,
                vol_total_mercado, participacao_clamed
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """  
        
        dados = []
        for _, row in df_validos.iterrows():
            try:
                registro = (
                    int(row['COD_BRICK']),
                    str(row['EAN']).strip(),
                    str(row['COD_PRODUTO']).strip(),
                    float(row['CONCORRENTE_SI']),
                    float(row['CONCORRENTE_SO']),
                    float(row['PRECO_POPULAR']),
                    float(row['VOL_TOTAL_MERCADO']),
                    float(row['PARTICIPACAO_CLAMED'])
                )
                dados.append(registro)
            except Exception as e:
                stats['erros'].append(f"Erro ao processar linha: {e}")
                continue
        
        print(f"   Dados preparados: {len(dados)} registros")
        
        inseridos = 0
        batch_size = 1000
        
        for i in range(0, len(dados), batch_size):
            batch = dados[i:i + batch_size]
            
            try:
                cursor.executemany(query, batch)
                inseridos += cursor.rowcount
                
                progresso = min(i + batch_size, len(dados))
                print(f"   Progresso: {progresso}/{len(dados)} registros", end='\r')
                
            except psycopg2.Error as e:
                conn.rollback()
                stats['erros'].append(f"Erro no lote {i//batch_size}: {e}")
                print(f"\n Erro no lote: {e}")
                continue
        
        print(f"\n   Registros processados: {inseridos}")
        
        # Commit
        conn.commit()
        stats['inseridos'] = inseridos
        
    except Exception as e:
        if conn:
            conn.rollback()
        stats['erros'].append(f"Erro geral: {e}")
        print(f" Erro no load_iqvia: {e}")
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        
        stats['fim'] = datetime.now()
        stats['duracao'] = (stats['fim'] - stats['inicio']).total_seconds()
        
        print(f" LOAD IQVIA finalizado em {stats['duracao']:.2f}s")
        print(f"   Inseridos/atualizados: {stats['inseridos']}")
    
    return stats