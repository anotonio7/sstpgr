from main import app, db
from sqlalchemy import text

with app.app_context():
    # Atualiza exames antigos com valor padrão
    db.session.execute(text("UPDATE s2220_exame SET descricao_atividade = 'Nao informada' WHERE descricao_atividade IS NULL"))
    db.session.commit()
    print("Exames antigos atualizados com 'Nao informada'")