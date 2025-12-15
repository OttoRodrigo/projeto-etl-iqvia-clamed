import sys
import os
from pathlib import Path
from typing import Dict
from datetime import datetime

print("=" * 60)
print("  INICIANDO ETL - CLAMED/IQVIA")
print("=" * 60)

BASE_DIR = Path(__file__).parent
print(f"  Diretório base: {BASE_DIR}")

ETL_DIR = BASE_DIR / "etl"
print(f"  Pasta ETL: {ETL_DIR}")

DATA_DIR = BASE_DIR.parent / "data"
print(f"  Pasta DATA: {DATA_DIR}")

RAW_DATA_DIR = DATA_DIR / "raw"

print(f"\n  Verificando estrutura...")

if not ETL_DIR.exists():
    print(f"  ERRO: Pasta 'etl' não encontrada em {ETL_DIR}")
    print("   Crie a pasta 'etl' com os arquivos:")
    print("   - extract.py")
    print("   - transform.py")
    print("   - load.py")
    sys.exit(1)

if not DATA_DIR.exists():
    print(f"  ERRO: Pasta 'data' não encontrada em {DATA_DIR}")
    print("   Crie a pasta 'data' com os arquivos .xlsx")
    sys.exit(1)

if RAW_DATA_DIR.exists():
    print(f"  Pasta raw encontrada: {RAW_DATA_DIR}")
    DATA_SOURCE_DIR = RAW_DATA_DIR
else:
    print(f"   Pasta 'raw' não encontrada, usando {DATA_DIR}")
    DATA_SOURCE_DIR = DATA_DIR

sys.path.insert(0, str(ETL_DIR))

try:
    from extract import extrair_filiais, extrair_IQVIA
    from transform import transformar_filiais, transformar_IQVIA
    from load import load_filiais, load_iqvia
    print("\n  Módulos importados com sucesso!")
    
except ImportError as e:
    print(f"\n  Erro ao importar módulos: {e}")
    print(f"\n  Conteúdo da pasta etl/:")
    for arquivo in ETL_DIR.iterdir():
        print(f"  - {arquivo.name}")
    sys.exit(1)

def configurar_db() -> Dict[str, str]:
    """
    Retorna configuração do banco de dados.
    Modifique com suas credenciais.
    """
    return {
        'dbname': 'postgresql',           
        'user': 'postgres',               
        'password': '12345',              
        'port': 5432,                     
        'host': 'localhost'               
    }

def encontrar_arquivo(pasta: Path, padroes: list) -> str:
    """Encontra um arquivo baseado em padrões."""
    for padrao in padroes:
        arquivos = list(pasta.glob(padrao))
        if arquivos:
            return str(arquivos[0])
    return ""

def validar_arquivos(caminho_filiais: str, caminho_iqvia: str) -> bool:
    """Verifica se os arquivos existem."""
    if not os.path.exists(caminho_filiais):
        print(f"  Arquivo não encontrado: {caminho_filiais}")
        print(f"   Arquivos disponíveis em {DATA_SOURCE_DIR}:")
        for arquivo in DATA_SOURCE_DIR.iterdir():
            if arquivo.is_file():
                print(f"     - {arquivo.name}")
        return False
    
    if not os.path.exists(caminho_iqvia):
        print(f"  Arquivo não encontrado: {caminho_iqvia}")
        return False
    
    return True

def executar_pipeline_completo():
    """
    Função principal que executa o pipeline ETL completo.
    """
    print("\n" + "=" * 60)
    print("  INICIANDO PIPELINE ETL COMPLETO")
    print("=" * 60)
    
    print(f"\n  Procurando arquivos em: {DATA_SOURCE_DIR}")
    
    padroes_filiais = ["*filia*.xlsx", "*filia*.xls", "*filial*.xlsx", "*filial*.xls"]
    padroes_iqvia = ["*iqvia*.xlsx", "*iqvia*.xls", "*IQVIA*.xlsx", "*IQVIA*.xls"]
    
    caminho_filiais = encontrar_arquivo(DATA_SOURCE_DIR, padroes_filiais)
    caminho_iqvia = encontrar_arquivo(DATA_SOURCE_DIR, padroes_iqvia)
    
    if not caminho_filiais:
        print(f"  Nenhum arquivo de filiais encontrado!")
        print(f"   Procurei por: {', '.join(padroes_filiais)}")
        return
    
    if not caminho_iqvia:
        print(f"  Nenhum arquivo do IQVIA encontrado!")
        print(f"   Procurei por: {', '.join(padroes_iqvia)}")
        return
    
    print(f"  Arquivo de filiais: {os.path.basename(caminho_filiais)}")
    print(f"  Arquivo do IQVIA: {os.path.basename(caminho_iqvia)}")
    
    # Configurar banco
    db_config = configurar_db()
    
    # Iniciar timer
    tempo_inicio = datetime.now()
    
    try:
        # 1. EXTRACT
        print("\n  ETAPA 1: EXTRACTION")
        print("   Extraindo filiais...")
        df_filiais_raw = extrair_filiais(caminho_filiais)
        print(f"     Filiais extraídas: {df_filiais_raw.shape}")
        
        print("   Extraindo IQVIA...")
        df_iqvia_raw = extrair_IQVIA(caminho_iqvia)
        print(f"    IQVIA extraído: {df_iqvia_raw.shape}")
        
        # 2. TRANSFORM
        print("\n ETAPA 2: TRANSFORMATION")
        print("   Transformando filiais...")
        df_filiais_transformed = transformar_filiais(df_filiais_raw)
        print(f"     Filiais transformadas: {df_filiais_transformed.shape}")
        print(f"   Colunas: {list(df_filiais_transformed.columns)}")
        
        print("   Transformando IQVIA...")
        df_iqvia_transformed = transformar_IQVIA(df_iqvia_raw)
        print(f"     IQVIA transformado: {df_iqvia_transformed.shape}")
        print(f"   Colunas: {list(df_iqvia_transformed.columns)}")
        
        # 3. LOAD
        print("\n  ETAPA 3: LOAD (PostgreSQL)")
        
        print("   Carregando filiais no banco...")
        stats_filiais = load_filiais(df_filiais_transformed, db_config, modo='upsert')
        
        print("   Carregando IQVIA no banco...")
        stats_iqvia = load_iqvia(df_iqvia_transformed, db_config, modo='upsert')
        
        # 4. RELATÓRIO FINAL
        print("\n" + "=" * 60)
        print("  RELATÓRIO FINAL DO PROCESSAMENTO")
        print("=" * 60)
        
        tempo_fim = datetime.now()
        duracao_total = (tempo_fim - tempo_inicio).total_seconds()
        
        print(f"⏱   Duração total: {duracao_total:.2f} segundos")
        
        print(f"\n  FILIAIS:")
        print(f"   • Processados: {stats_filiais.get('total_processados', 0)}")
        print(f"   • Válidos: {stats_filiais.get('registros_validos', 0)}")
        print(f"   • Inseridos: {stats_filiais.get('inseridos', 0)}")
        
        print(f"\n  IQVIA:")
        print(f"   • Processados: {stats_iqvia.get('total_processados', 0)}")
        print(f"   • Válidos: {stats_iqvia.get('registros_validos', 0)}")
        print(f"   • Inseridos: {stats_iqvia.get('inseridos', 0)}")
        print(f"   • Data carga: {stats_iqvia.get('data_carga', 'N/A')}")
        
        df_filiais_transformed.to_csv('filiais_transformadas.csv', index=False, encoding='utf-8-sig')
        df_iqvia_transformed.to_csv('iqvia_transformado.csv', index=False, encoding='utf-8-sig')
        print(f"\n  Dados transformados salvos em CSV:")
        print(f"   • filiais_transformadas.csv")
        print(f"   • iqvia_transformado.csv")
        
        print(f"\n  PIPELINE CONCLUÍDO COM SUCESSO!")
        
    except Exception as e:
        print(f"\n  ERRO NO PROCESSAMENTO: {e}")
        import traceback
        traceback.print_exc()

def executar_apenas_transform():
    """
    Executa apenas extract e transform (sem load no banco).
    """
    print("\n" + "=" * 60)
    print(" EXECUTANDO APENAS EXTRACT + TRANSFORM")
    print("=" * 60)
    
    print(f"\n  Procurando arquivos em: {DATA_SOURCE_DIR}")
    
    padroes_filiais = ["*filia*.xlsx", "*filia*.xls", "*filial*.xlsx", "*filial*.xls"]
    padroes_iqvia = ["*iqvia*.xlsx", "*iqvia*.xls", "*IQVIA*.xlsx", "*IQVIA*.xls"]
    
    caminho_filiais = encontrar_arquivo(DATA_SOURCE_DIR, padroes_filiais)
    caminho_iqvia = encontrar_arquivo(DATA_SOURCE_DIR, padroes_iqvia)
    
    if not caminho_filiais:
        print(f"  Nenhum arquivo de filiais encontrado!")
        return
    
    if not caminho_iqvia:
        print(f"  Nenhum arquivo do IQVIA encontrado!")
        return
    
    try:
        # Extract
        print("\n  Extraindo dados...")
        df_filiais = extrair_filiais(caminho_filiais)
        df_iqvia = extrair_IQVIA(caminho_iqvia)
        print(f"  Filiais: {df_filiais.shape}")
        print(f"  IQVIA: {df_iqvia.shape}")
        
        # Transform
        print("\n  Transformando dados...")
        df_filiais_t = transformar_filiais(df_filiais)
        df_iqvia_t = transformar_IQVIA(df_iqvia)
        print(f"  Filiais transformadas: {df_filiais_t.shape}")
        print(f"  IQVIA transformado: {df_iqvia_t.shape}")
        
        print("\n Salvando resultados...")
        df_filiais_t.to_excel('output_filiais_transformado.xlsx', index=False)
        df_iqvia_t.to_excel('output_iqvia_transformado.xlsx', index=False)
        
        print(f"\n  Dados transformados salvos:")
        print(f"   • output_filiais_transformado.xlsx")
        print(f"   • output_iqvia_transformado.xlsx")
        
        print(f"\n  AMOSTRA FILIAIS (5 primeiras):")
        print(df_filiais_t.head())
        
        print(f"\n AMOSTRA IQVIA (3 primeiras):")
        print(df_iqvia_t.head(3))
        
    except Exception as e:
        print(f"\n  Erro: {e}")
        import traceback
        traceback.print_exc()

def testar_conexao_banco():
    """Testa conexão com o banco de dados."""
    print("\n" + "=" * 60)
    print("🔗 TESTANDO CONEXÃO COM BANCO DE DADOS")
    print("=" * 60)
    
    try:
        from database import connect_db
        db_config = configurar_db()
        
        print(f"\n  Tentando conectar com:")
        print(f"   Host: {db_config['host']}")
        print(f"   Porta: {db_config['port']}")
        print(f"   Banco: {db_config['dbname']}")
        print(f"   Usuário: {db_config['user']}")
        
        conn = connect_db(**db_config)
        print("\n  Conexão com banco estabelecida com sucesso!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   PostgreSQL version: {version}")
        
        cursor.close()
        conn.close()
        print("   Conexão fechada.")
        
    except Exception as e:
        print(f"\n  Falha na conexão: {e}")

if __name__ == "__main__":
    
    while True:
        print("\n" + "=" * 60)
        print("  MENU PRINCIPAL - ETL CLAMED/IQVIA")
        print("=" * 60)
        print("1. Pipeline completo (Extract + Transform + Load)")
        print("2. Apenas Extract + Transform (sem banco)")
        print("3. Testar conexão com banco")
        print("4. Sair")
        
        try:
            opcao = input("\n  Digite a opção (1-4): ").strip()
            
            if opcao == "1":
                executar_pipeline_completo()
            elif opcao == "2":
                executar_apenas_transform()
            elif opcao == "3":
                testar_conexao_banco()
            elif opcao == "4":
                print("\n  Até logo!")
                break
            else:
                print("  Opção inválida. Use 1, 2, 3 ou 4.")
                
            if opcao in ["1", "2", "3"]:
                continuar = input("\n   Executar novamente? (s/n): ").strip().lower()
                if continuar != 's':
                    print("\n  Até logo!")
                    break
                
        except KeyboardInterrupt:
            print("\n\n   Processo interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"\n  Erro inesperado: {e}")