from main import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text('ALTER TABLE evento_s2221 ADD COLUMN cpf_responsavel VARCHAR(14)'))
        db.session.commit()
        print("Coluna 'cpf_responsavel' adicionada com sucesso!")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("Coluna já existe, nada a fazer.")
        else:
            print(f"Erro: {e}")