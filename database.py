import sqlite3
# Constante com o nome do arquivo de banco de dados.
# O arquivo ordens.db será criado automaticamente na primeira execução.
NOME_BANCO = "ordens.db"


def get_connection():
    """
    Cria e retorna uma conexão com o banco de dados SQLite.
    A propriedade row_factory permite acessar as colunas pelo nome
    (ex: ordem['produto']) em vez de pelo índice (ex: ordem[1]).
    Retorna:
    sqlite3.Connection: objeto de conexão com o banco de dados.
    """
    conn = sqlite3.connect(NOME_BANCO)
    conn.row_factory = sqlite3.Row
    return conn



def init_db():
    """
    Inicializa o banco de dados criando a tabela 'ordens' se ela
    ainda não existir. Seguro para chamar múltiplas vezes.
    """
 
    conn = get_connection()
    # cursor() permite executar comandos SQL
    cursor = conn.cursor()
    
    # IF NOT EXISTS garante que o comando não falha se a tabela já existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordens (
            id          INTEGER     PRIMARY KEY AUTOINCREMENT,
            produto     TEXT        NOT NULL,
            quantidade  INTEGER     NOT NULL,
            status      TEXT        DEFAULT 'Pendente',
            criado_em   TEXT        DEFAULT (datetime('now', 'localtime'))
        )
        ''')
    
    # commit() salva as alterações no arquivo .db
    conn.commit()
    # close() libera a conexão (boa prática)
    conn.close()
    print("Banco de dados inicializado com sucesso.")
    
init_db()