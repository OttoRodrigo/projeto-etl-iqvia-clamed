CREATE TABLE dim_brick_filial (
    cod_brick INTEGER,
    cod_filial INTEGER,
    nome_brick VARCHAR(255),
    
    PRIMARY KEY (cod_brick, cod_filial)
);

COMMENT ON TABLE dim_brick_filial IS 'Relação entre bricks e filiais (1 brick → N filiais)';
COMMENT ON COLUMN dim_brick_filial.cod_brick IS 'Código do brick (parte da PK)';
COMMENT ON COLUMN dim_brick_filial.cod_filial IS 'Código da filial (parte da PK)';
COMMENT ON COLUMN dim_brick_filial.nome_brick IS 'Nome do brick para referência';