import pandas as pd
from typing import Optional

def extrair_filiais(path: str, dtypes: Optional[dict] = None, sheet_name: Optional[str | int] = 0) -> pd.DataFrame:
    """
    Extrai dados de filiais de um arquivo Excel.
    
    Args:
        path (str): Caminho do arquivo Excel
        dtypes (dict, optional): Dicionário com tipos de dados para as colunas
        sheet_name (str | int, optional): Nome ou índice da planilha. Padrão: 0
    
    Returns:
        pd.DataFrame: DataFrame com os dados das filiais
    """
    try:
        df = pd.read_excel(
            path,
            dtype=dtypes,  
            sheet_name=sheet_name
        )
        
        print(f"Arquivo carregado: {path}")
        print(f"Shape: {df.shape}")
        print(f"Colunas: {list(df.columns)}")
        
        return df
        
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {path}")
        return pd.DataFrame()  
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return pd.DataFrame()

def extrair_IQVIA(path: str, sheet_name: Optional[str | int] = 0) -> pd.DataFrame:
    """
    Extrai dados de arquivos IQVIA sem tratativas especiais.
    
    Args:
        path (str): Caminho do arquivo Excel
        sheet_name (str | int, optional): Nome ou índice da planilha. Padrão: 0
    
    Returns:
        pd.DataFrame: DataFrame com os dados da IQVIA
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
        print(f"Arquivo carregado: {path}")
        print(f"Shape: {df.shape}")
        print(f"Colunas: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return pd.DataFrame()