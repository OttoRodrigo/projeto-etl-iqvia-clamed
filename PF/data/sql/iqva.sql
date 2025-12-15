CREATE TABLE fact_iqvia (
    cod_brick INTEGER NOT NULL,
    ean VARCHAR(20) NOT NULL,
    cod_produto VARCHAR(20) NOT NULL,
    
    concorrente_si DECIMAL(15,2) DEFAULT 0.00,
    concorrente_so DECIMAL(15,2) DEFAULT 0.00,
    preco_popular DECIMAL(15,2) DEFAULT 0.00,
    vol_total_mercado DECIMAL(15,2) DEFAULT 0.00,
    participacao_clamed DECIMAL(5,4) DEFAULT 0.0000,
    
    PRIMARY KEY (cod_brick, ean, cod_produto)
);

COMMENT ON TABLE fact_iqvia IS 'Dados IQVIA - relação por cod_brick';
COMMENT ON COLUMN fact_iqvia.cod_brick IS 'Código do brick (relaciona com dim_brick_filial)';
COMMENT ON COLUMN fact_iqvia.ean IS 'EAN do produto';
COMMENT ON COLUMN fact_iqvia.cod_produto IS 'Código interno do produto';
COMMENT ON COLUMN fact_iqvia.concorrente_si IS 'Vendas concorrente SI';
COMMENT ON COLUMN fact_iqvia.concorrente_so IS 'Vendas concorrente SO';
COMMENT ON COLUMN fact_iqvia.preco_popular IS 'Vendas Preço Popular';
COMMENT ON COLUMN fact_iqvia.vol_total_mercado IS 'Volume total mercado';
COMMENT ON COLUMN fact_iqvia.participacao_clamed IS 'Participação Clamed (0-1)';