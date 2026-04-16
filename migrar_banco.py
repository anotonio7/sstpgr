# migrar_banco.py
from main import app, db
from sqlalchemy import text


def migrar():
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            resultado = db.session.execute(text("PRAGMA table_info(empresa)"))
            colunas = [row[1] for row in resultado]

            if 'usuario_id' not in colunas:
                print("Adicionando coluna usuario_id na tabela empresa...")
                db.session.execute(text("ALTER TABLE empresa ADD COLUMN usuario_id INTEGER"))
                db.session.execute(
                    text("ALTER TABLE empresa ADD COLUMN usuario_id_tmp INTEGER REFERENCES usuarios(id)"))
                # SQLite não suporta ADD CONSTRAINT diretamente, então renomeamos
                db.session.commit()
                print("Coluna adicionada com sucesso!")
            else:
                print("Coluna usuario_id já existe!")

        except Exception as e:
            print(f"Erro: {e}")
            db.session.rollback()


if __name__ == "__main__":
    migrar()
    print("Migração concluída!")