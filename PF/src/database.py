import psycopg2 as pg

def connect_db(dbname, user, password, port, host):
    try:
        return pg.connect(
            dbname=dbname,
            user=user,
            password=password,
            port= port,
            host=host
        )
    except:
        print("Erro: Falha ao se conectar com o banco!")