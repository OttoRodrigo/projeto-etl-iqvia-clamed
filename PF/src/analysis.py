import pandas as pd
import numpy as np
from database import connect_db
from typing import Dict
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def configurar_db() -> Dict[str, str]:
    """
    Retorna configuração do banco de dados.
    """
    return {
        'dbname': 'postgresql',
        'user': 'postgres',
        'password': '12345',
        'port': 5432,
        'host': 'localhost'
    }

def validar_etl():
    """
    Valida se o ETL funcionou corretamente.
    """
    print("=" * 60)
    print("  VALIDAÇÃO DO ETL - CLAMED/IQVIA")
    print("=" * 60)
    
    db_config = configurar_db()
    conn = None
    cursor = None
    
    try:
        conn = connect_db(**db_config)
        cursor = conn.cursor()
        print(" Conectado ao banco de dados")
        
        print("\n1.  VERIFICANDO TABELAS:")
        
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('dim_brick_filial', 'fact_iqvia')
        ORDER BY table_name;
        """)
        
        tabelas = cursor.fetchall()
        tabelas_encontradas = [t[0] for t in tabelas]
        
        print(f"   Tabelas encontradas: {tabelas_encontradas}")
        
        if len(tabelas_encontradas) != 2:
            print(f"     Esperadas 2 tabelas, encontradas {len(tabelas_encontradas)}")
            return False
        
        print("\n2.  CONTAGEM DE REGISTROS:")
        
        cursor.execute("SELECT COUNT(*) as total FROM dim_brick_filial;")
        total_filiais = cursor.fetchone()[0]
        print(f"   dim_brick_filial: {total_filiais} registros")
        
        cursor.execute("SELECT COUNT(*) as total FROM fact_iqvia;")
        total_iqvia = cursor.fetchone()[0]
        print(f"   fact_iqvia: {total_iqvia} registros")
        
        if total_filiais == 0 or total_iqvia == 0:
            print("     Uma ou ambas tabelas estão vazias!")
            return False
        
        print("\n3.  GERANDO GRÁFICOS DE INSIGHTS:")
        
        gerar_grafico_comparativo_concorrentes(cursor)
        gerar_grafico_distribuicao_vendas(cursor)
        
        print("\n" + "=" * 60)
        print(" VALIDAÇÃO E GRÁFICOS CONCLUÍDOS")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f" Erro na validação: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def gerar_grafico_comparativo_concorrentes(cursor):
    """
    Gráfico de Barras: Comparativo de Volume Total Concorrentes vs. Volume Clamed (PP) por Brick.
    """
    try:
        query_top_bricks = """
        SELECT 
            f.cod_brick,
            d.nome_brick,
            SUM(f.concorrente_si + f.concorrente_so) as total_concorrentes,
            SUM(f.preco_popular) as total_pp,
            SUM(f.vol_total_mercado) as total_mercado
        FROM fact_iqvia f
        LEFT JOIN dim_brick_filial d ON f.cod_brick = d.cod_brick
        GROUP BY f.cod_brick, d.nome_brick
        HAVING SUM(f.vol_total_mercado) > 0
        ORDER BY SUM(f.vol_total_mercado) DESC
        LIMIT 10;
        """
        
        cursor.execute(query_top_bricks)
        colunas = ['cod_brick', 'nome_brick', 'total_concorrentes', 'total_pp', 'total_mercado']
        dados = cursor.fetchall()
        
        if not dados:
            print("     Não há dados suficientes para gerar gráfico de concorrentes")
            return
        
        df = pd.DataFrame(dados, columns=colunas)
        
        df['rotulo'] = df.apply(lambda x: f"{x['cod_brick']}\n{x['nome_brick'][:15]}...", axis=1)
        
        plt.figure(figsize=(12, 6))
        
        x = range(len(df))
        largura = 0.35
        
        plt.bar([i - largura/2 for i in x], df['total_concorrentes'], 
                width=largura, label='Concorrentes (SI+SO)', alpha=0.8)
        plt.bar([i + largura/2 for i in x], df['total_pp'], 
                width=largura, label='Clamed (PP)', alpha=0.8)
        
        plt.title('Comparativo: Concorrentes vs Clamed por Brick (Top 10)', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Brick', fontsize=12)
        plt.ylabel('Volume Total', fontsize=12)
        plt.xticks(x, df['rotulo'], rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        for i, (conc, pp) in enumerate(zip(df['total_concorrentes'], df['total_pp'])):
            plt.text(i - largura/2, conc, f'{conc:,.0f}', 
                    ha='center', va='bottom', fontsize=9)
            plt.text(i + largura/2, pp, f'{pp:,.0f}', 
                    ha='center', va='bottom', fontsize=9)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"grafico_concorrentes_vs_clamed_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    Gráfico 1 salvo: {filename}")
        
        print(f"\n    RESUMO TOP BRICKS:")
        for _, row in df.head(5).iterrows():
            participacao = (row['total_pp'] / row['total_mercado'] * 100) if row['total_mercado'] > 0 else 0
            print(f"      Brick {row['cod_brick']}:")
            print(f"        • Concorrentes: R$ {row['total_concorrentes']:,.2f}")
            print(f"        • Clamed: R$ {row['total_pp']:,.2f}")
            print(f"        • Participação: {participacao:.1f}%")
        
    except Exception as e:
        print(f"    Erro ao gerar gráfico de concorrentes: {e}")

def gerar_grafico_distribuicao_vendas(cursor):
    """
    Gráfico de Dispersão: Distribuição de vendas dos produtos.
    """
    try:
        query_produtos = """
        SELECT 
            ean,
            cod_produto,
            SUM(preco_popular) as total_vendas_pp,
            SUM(vol_total_mercado) as total_mercado,
            COUNT(*) as qtd_registros,
            AVG(participacao_clamed) as media_participacao
        FROM fact_iqvia
        WHERE preco_popular > 0
        GROUP BY ean, cod_produto
        HAVING SUM(preco_popular) > 0
        ORDER BY SUM(preco_popular) DESC
        LIMIT 50;
        """
        
        cursor.execute(query_produtos)
        colunas = ['ean', 'cod_produto', 'total_vendas_pp', 'total_mercado', 
                  'qtd_registros', 'media_participacao']
        dados = cursor.fetchall()
        
        if not dados:
            print("     Não há dados suficientes para gerar gráfico de produtos")
            return
        
        df = pd.DataFrame(dados, columns=colunas)
        
        df['total_vendas_pp'] = pd.to_numeric(df['total_vendas_pp'], errors='coerce')
        df['total_mercado'] = pd.to_numeric(df['total_mercado'], errors='coerce')
        df['media_participacao'] = pd.to_numeric(df['media_participacao'], errors='coerce')
        df['qtd_registros'] = pd.to_numeric(df['qtd_registros'], errors='coerce')
        
        df = df.dropna(subset=['total_vendas_pp', 'total_mercado', 'media_participacao', 'qtd_registros'])
        
        if df.empty:
            print("     Não há dados válidos após limpeza")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        axes[0].hist(df['total_vendas_pp'], bins=15, edgecolor='black', alpha=0.7)
        axes[0].set_title('Distribuição de Vendas por Produto', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Vendas Clamed (R$)', fontsize=10)
        axes[0].set_ylabel('Quantidade de Produtos', fontsize=10)
        axes[0].grid(True, alpha=0.3)
        
        media_vendas = df['total_vendas_pp'].mean()
        mediana_vendas = df['total_vendas_pp'].median()
        axes[0].axvline(media_vendas, color='red', linestyle='--', linewidth=2, 
                       label=f'Média: R$ {media_vendas:,.2f}')
        axes[0].axvline(mediana_vendas, color='green', linestyle='--', linewidth=2,
                       label=f'Mediana: R$ {mediana_vendas:,.2f}')
        axes[0].legend()
        
        tamanhos = df['total_mercado'] / df['total_mercado'].max() * 500  # Normalizar entre 0 e 500
        
        tamanhos = np.array(tamanhos, dtype=float)
        
        scatter = axes[1].scatter(df['total_vendas_pp'], df['media_participacao'] * 100,
                                 c=df['qtd_registros'], cmap='viridis', 
                                 s=tamanhos, alpha=0.6, edgecolors='w', linewidth=0.5)
        
        axes[1].set_title('Vendas vs Participação (Tamanho = Mercado Total)', 
                         fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Vendas Clamed (R$)', fontsize=10)
        axes[1].set_ylabel('Participação Média (%)', fontsize=10)
        axes[1].grid(True, alpha=0.3)
        
        plt.colorbar(scatter, ax=axes[1], label='Quantidade de Registros')
        
        if len(df) > 1:
            mask = (df['total_vendas_pp'] < df['total_vendas_pp'].quantile(0.95)) & \
                   (df['media_participacao'] * 100 < df['media_participacao'].quantile(0.95) * 100)
            
            if mask.sum() > 1:  
                z = np.polyfit(df.loc[mask, 'total_vendas_pp'], 
                              df.loc[mask, 'media_participacao'] * 100, 1)
                p = np.poly1d(z)
                x_range = np.linspace(df['total_vendas_pp'].min(), 
                                     df['total_vendas_pp'].max(), 100)
                axes[1].plot(x_range, p(x_range), "r--", alpha=0.8, linewidth=2)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"grafico_distribuicao_vendas_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"    Gráfico 2 salvo: {filename}")
        
        print(f"\n    TOP 5 PRODUTOS POR VENDAS:")
        for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
            print(f"      {i}. EAN: {row['ean']}")
            print(f"         • Vendas PP: R$ {row['total_vendas_pp']:,.2f}")
            print(f"         • Participação: {row['media_participacao']*100:.1f}%")
            print(f"         • Registros: {row['qtd_registros']}")
        
    except Exception as e:
        print(f"    Erro ao gerar gráfico de distribuição: {e}")
        import traceback
        traceback.print_exc()

def gerar_relatorio_completo():
    """
    Gera relatório completo com validação e gráficos.
    """
    print("=" * 60)
    print(" RELATÓRIO COMPLETO DE ANÁLISE")
    print("=" * 60)
    
    sucesso = validar_etl()
    
    if sucesso:
        print("\n" + "=" * 60)
        print(" RELATÓRIO CONCLUÍDO!")
        print("=" * 60)
        print("\n Arquivos gerados:")
        print("   • Gráfico comparativo concorrentes vs clamed")
        print("   • Gráfico distribuição de vendas")
        print("\n Análise finalizada com sucesso!")
    else:
        print("\n Não foi possível gerar relatório completo")

if __name__ == "__main__":
    """
    Ponto de entrada do script.
    """
    print("ANÁLISE E VALIDAÇÃO DO ETL - CLAMED/IQVIA")
    print("=" * 60)
    print("Selecione a opção:")
    print("1. Validar ETL (com gráficos)")
    print("2. Relatório completo (validação + gráficos)")
    print("3. Apenas gerar gráficos")
    
    try:
        opcao = input("\n Digite a opção (1-3): ").strip()
        
        if opcao == "1":
            validar_etl()
        elif opcao == "2":
            gerar_relatorio_completo()
        elif opcao == "3":
            db_config = configurar_db()
            conn = connect_db(**db_config)
            cursor = conn.cursor()
            
            print("\n GERANDO APENAS GRÁFICOS:")
            gerar_grafico_comparativo_concorrentes(cursor)
            gerar_grafico_distribuicao_vendas(cursor)
            
            cursor.close()
            conn.close()
        else:
            print(" Opção inválida")
            
    except KeyboardInterrupt:
        print("\n\n  Processo interrompido")
    except Exception as e:
        print(f"\n Erro: {e}")