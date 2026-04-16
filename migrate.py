import sqlite3

conn = sqlite3.connect('sst2.db')
cursor = conn.cursor()
cursor.execute("ALTER TABLE funcionario ADD COLUMN matricula_esocial VARCHAR(50)")
conn.commit()
conn.close()
print("Coluna adicionada com sucesso!")