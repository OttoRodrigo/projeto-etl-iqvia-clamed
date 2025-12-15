Projeto PF - Pipeline ETL
=========================

Descrição
---------

Este repositório contém um pipeline ETL simples em Python para extração, transformação e carga de dados, além de scripts de análise e utilitários de banco de dados usados no projeto.

Estrutura do repositório
------------------------

- data/: arquivos brutos, modelo relacional e scripts SQL
- src/: código fonte do projeto
	- [src/main.py](src/main.py) - ponto de entrada para execução
	- [src/database.py](src/database.py) - utilitários de conexão/CRUD com o banco
	- [src/analysis.py](src/analysis.py) - scripts de análise/validação
	- src/etl/: pacotes ETL
		- [src/etl/extract.py](src/etl/extract.py) - extração de dados
		- [src/etl/transform.py](src/etl/transform.py) - transformação/limpeza
		- [src/etl/load.py](src/etl/load.py) - carregamento para destino

Requisitos
----------

- Python 3.8+
- Dependências listadas em `requirements.txt`

Instalação (Windows - PowerShell)
--------------------------------

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Uso
---

1. Ative o ambiente virtual (veja comandos acima).
2. Execute o pipeline com:

```powershell
python src/main.py
```

3. Para executar análises ou scripts isolados, rode os módulos correspondentes, por exemplo:

```powershell
python src/analysis.py
```

Como o ETL está organizado
-------------------------

- Extração: funções em [src/etl/extract.py](src/etl/extract.py) responsáveis por ler arquivos em `data/raw/` ou consultar fontes.
- Transformação: lógica de limpeza e padronização em [src/etl/transform.py](src/etl/transform.py).
- Carga: inserção/atualização no banco via [src/etl/load.py](src/etl/load.py) e [src/database.py](src/database.py).
