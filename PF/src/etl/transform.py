import pandas as pd

def transformar_filiais(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma filiais separando BRICK em código e nome.
    """
    if df.empty:
        return df
    
    df_transformado = df.copy()
    
    df_transformado.columns = df_transformado.columns.str.strip()
    
    brick_col = None
    for col in df_transformado.columns:
        if 'brick' in str(col).lower():
            brick_col = col
            break
    
    if not brick_col:
        print(" Coluna BRICK não encontrada")
        return df_transformado
    
    def separar_brick(valor):
        if pd.isna(valor):
            return (None, "Não identificado")
        
        valor_str = str(valor).strip()
        partes = valor_str.split(' - ', 1)
        
        if len(partes) >= 2:
            codigo = partes[0].strip()
            nome = partes[1].strip()
        elif len(partes) == 1:
            codigo = partes[0].strip() if partes[0].strip().isdigit() else "0"
            nome = "Não identificado"
        else:
            codigo = "0"
            nome = "Não identificado"
        
        return (codigo, nome)
    
    df_transformado[['COD_BRICK', 'NOME_BRICK']] = pd.DataFrame(
        df_transformado[brick_col].apply(separar_brick).tolist(),
        index=df_transformado.index
    )
    
    df_transformado['COD_BRICK'] = pd.to_numeric(
        df_transformado['COD_BRICK'], 
        errors='coerce'
    ).fillna(0).astype(int)
    
    cod_filial_col = None
    for col in df_transformado.columns:
        if any(x in str(col).lower() for x in ['cód', 'cod', 'filial']):
            cod_filial_col = col
            break
    
    if cod_filial_col:
        df_transformado = df_transformado.rename(columns={cod_filial_col: 'COD_FILIAL'})
        
        df_transformado['PK_FILIAL'] = (
            df_transformado['COD_BRICK'].astype(str) + '_' + 
            df_transformado['COD_FILIAL'].astype(str)
        )
    
    if 'COD_FILIAL' in df_transformado.columns:
        antes = len(df_transformado)
        df_transformado = df_transformado.dropna(subset=['COD_FILIAL'])
        df_transformado = df_transformado[df_transformado['COD_FILIAL'] != '']
        removidos = antes - len(df_transformado)
        print(f"  Filiais removidas (código vazio): {removidos}")
    
    print(f" Filiais transformadas: {len(df_transformado)} registros")
    print(f"   Códigos BRICK únicos: {df_transformado['COD_BRICK'].nunique()}")
    print(f"   Filiais únicas: {df_transformado['COD_FILIAL'].nunique()}")
    
    return df_transformado

def transformar_IQVIA(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma dados IQVIA 
    """
    
    if df.empty:
        print(" DataFrame IQVIA vazio")
        return df
    
    df_transformado = df.copy()
    
    print(f" Iniciando transformação IQVIA: {df_transformado.shape}")
    
    df_transformado.columns = (
        df_transformado.columns
        .str.strip()
        .str.upper()
        .str.replace(' ', '_')
        .str.replace('Ã', 'A')
        .str.replace('Ç', 'C')
        .str.replace('Á', 'A')
        .str.replace('É', 'E')
        .str.replace('Í', 'I')
        .str.replace('Ó', 'O')
        .str.replace('Ú', 'U')
    )
    
    print(f"   Colunas após padronização: {list(df_transformado.columns)}")
    
    rename_dict = {}
    for col in df_transformado.columns:
        new_name = col
        
        if 'BRICK' in col:
            new_name = 'BRICK'
        elif 'EAN' in col:
            new_name = 'EAN'
        elif 'COD_PROD' in col or 'CATARINENSE' in col:
            new_name = 'COD_PRODUTO'
        elif 'SI_BANDEIRA_CONCORRENTE' in col:
            new_name = 'CONCORRENTE_SI'
        elif 'SO_BANDEIRA_CONCORRENTE' in col:
            new_name = 'CONCORRENTE_SO'
        elif 'PRECO_POPULAR' in col or 'PP' in col:
            new_name = 'PRECO_POPULAR'
        
        if new_name != col:
            rename_dict[col] = new_name
    
    if rename_dict:
        df_transformado = df_transformado.rename(columns=rename_dict)
        print(f"   Colunas renomeadas: {rename_dict}")
    
    brick_col = 'BRICK'
    if brick_col in df_transformado.columns:
        def separar_brick(valor):
            if pd.isna(valor):
                return (0, "NAO_IDENTIFICADO")
            
            valor_str = str(valor).strip()
            partes = valor_str.split(' - ', 1)
            
            if len(partes) >= 2:
                codigo = partes[0].strip()
                nome = partes[1].strip().replace(' - ', '_').replace(' ', '_')
            elif len(partes) == 1:
                codigo = partes[0].strip() if partes[0].strip().isdigit() else "0"
                nome = "NAO_IDENTIFICADO"
            else:
                codigo = "0"
                nome = "NAO_IDENTIFICADO"
            
            return (codigo, nome)
        
        df_transformado[['COD_BRICK', 'NOME_BRICK']] = pd.DataFrame(
            df_transformado[brick_col].apply(separar_brick).tolist(),
            index=df_transformado.index
        )
        
        df_transformado['COD_BRICK'] = pd.to_numeric(
            df_transformado['COD_BRICK'], 
            errors='coerce'
        ).fillna(0).astype(int)
        
        print(f"   BRICK separado: {df_transformado['COD_BRICK'].nunique()} códigos únicos")
    
    if 'EAN' in df_transformado.columns:
        df_transformado['EAN'] = (
            df_transformado['EAN']
            .astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)
            .str.zfill(13)
        )
        print(f"   EAN convertido para string: {df_transformado['EAN'].nunique()} valores únicos")
    
    if 'COD_PRODUTO' in df_transformado.columns:
        df_transformado['COD_PRODUTO'] = (
            df_transformado['COD_PRODUTO']
            .astype(str)
            .str.strip()
            .str.replace(r'\.0$', '', regex=True)
        )
        print(f"   COD_PRODUTO convertido: {df_transformado['COD_PRODUTO'].nunique()} produtos")
    
    colunas_numericas = ['CONCORRENTE_SI', 'CONCORRENTE_SO', 'PRECO_POPULAR']
    
    for col in colunas_numericas:
        if col in df_transformado.columns:
            df_transformado[col] = (
                df_transformado[col]
                .astype(str)
                .str.replace(',', '.', regex=False)
                .replace(['nan', 'NaN', 'NAN', 'None', 'NULL', ''], '0')
                .astype(float)
                .fillna(0)
                .round(2)
            )
            
            zeros_count = (df_transformado[col] == 0).sum()
            print(f"   {col}: {zeros_count} valores definidos como 0 (incluindo nulos)")
    
    col_calc_disponiveis = [c for c in ['CONCORRENTE_SI', 'CONCORRENTE_SO', 'PRECO_POPULAR'] 
                           if c in df_transformado.columns]
    
    if len(col_calc_disponiveis) >= 1:
        df_transformado['VOL_TOTAL_MERCADO'] = df_transformado[col_calc_disponiveis].sum(axis=1)
        
        if 'PRECO_POPULAR' in df_transformado.columns:
            df_transformado['PARTICIPACAO_CLAMED'] = (
                df_transformado['PRECO_POPULAR'] / df_transformado['VOL_TOTAL_MERCADO'].replace(0, 1)
            ).fillna(0).round(4)
        else:
            df_transformado['PARTICIPACAO_CLAMED'] = 0
        
        print(f"   Colunas calculadas criadas: VOL_TOTAL_MERCADO, PARTICIPACAO_CLAMED")
        
        vol_medio = df_transformado['VOL_TOTAL_MERCADO'].mean()
        part_media = df_transformado['PARTICIPACAO_CLAMED'].mean()
        print(f"   Volume médio mercado: {vol_medio:.2f}")
        print(f"   Participação média Clamed: {part_media:.2%}")
    
    chaves_duplicidade = []
    if 'EAN' in df_transformado.columns:
        chaves_duplicidade.append('EAN')
    if 'COD_PRODUTO' in df_transformado.columns:
        chaves_duplicidade.append('COD_PRODUTO')
    if 'COD_BRICK' in df_transformado.columns:
        chaves_duplicidade.append('COD_BRICK')
    
    if chaves_duplicidade:
        antes = len(df_transformado)
        df_transformado = df_transformado.drop_duplicates(subset=chaves_duplicidade)
        removidos = antes - len(df_transformado)
        
        print(f"   Duplicatas removidas: {removidos}")
        
        if removidos > 0:
            print(f"   Chaves usadas: {chaves_duplicidade}")
    
    colunas_ordenadas = []
    
    if 'COD_BRICK' in df_transformado.columns:
        colunas_ordenadas.append('COD_BRICK')
    if 'NOME_BRICK' in df_transformado.columns:
        colunas_ordenadas.append('NOME_BRICK')
    if 'BRICK' in df_transformado.columns:
        colunas_ordenadas.append('BRICK')
    if 'EAN' in df_transformado.columns:
        colunas_ordenadas.append('EAN')
    if 'COD_PRODUTO' in df_transformado.columns:
        colunas_ordenadas.append('COD_PRODUTO')
    
    colunas_ordenadas.extend([c for c in ['CONCORRENTE_SI', 'CONCORRENTE_SO', 'PRECO_POPULAR'] 
                              if c in df_transformado.columns])
    
    colunas_ordenadas.extend([c for c in ['VOL_TOTAL_MERCADO', 'PARTICIPACAO_CLAMED'] 
                              if c in df_transformado.columns])
    
    outras_colunas = [c for c in df_transformado.columns if c not in colunas_ordenadas]
    colunas_ordenadas.extend(outras_colunas)
    
    df_transformado = df_transformado[colunas_ordenadas]
    
    print(f"\n Transformação IQVIA concluída:")
    print(f"   Registros finais: {df_transformado.shape[0]}")
    print(f"   Colunas finais: {df_transformado.shape[1]}")
    print(f"   Colunas: {list(df_transformado.columns)}")
    
    if not df_transformado.empty:
        print(f"\n📋 Amostra dos dados transformados:")
        print(df_transformado.head(3).to_string())
    
    return df_transformado