import sqlite3

conn = sqlite3.connect('instance/sst.db')
cursor = conn.cursor()

# Lista todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tabelas encontradas:")
for table in tables:
    print(f"  - {table[0]}")

# Verifica se as tabelas que precisamos existem
tabelas_necessarias = ['clientes', 'avaliacoes_psicossociais']
for tabela in tabelas_necessarias:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabela}'")
    existe = cursor.fetchone()
    if existe:
        print(f"? Tabela '{tabela}' existe")
    else:
        print(f"? Tabela '{tabela}' N?O existe - ser? criada")
        if tabela == 'clientes':
            cursor.execute('''
                CREATE TABLE clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    empresa TEXT,
                    telefone TEXT,
                    data_cadastro TIMESTAMP
                )
            ''')
            print(f"   Tabela '{tabela}' criada!")
        elif tabela == 'avaliacoes_psicossociais':
            cursor.execute('''
                CREATE TABLE avaliacoes_psicossociais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    funcionario_id INTEGER,
                    token TEXT NOT NULL UNIQUE,
                    email_enviado INTEGER DEFAULT 0,
                    data_envio TIMESTAMP,
                    data_resposta TIMESTAMP,
                    status TEXT DEFAULT 'pendente',
                    respostas TEXT,
                    nome_funcionario TEXT,
                    cargo TEXT,
                    setor TEXT,
                    pontuacao_total INTEGER,
                    nivel_risco TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
                )
            ''')
            print(f"   Tabela '{tabela}' criada!")

conn.commit()
conn.close()

print("\n? Verifica??o conclu?da!")
