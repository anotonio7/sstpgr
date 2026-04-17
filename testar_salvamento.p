from main import app, db
from models import S2220Exame

with app.app_context():
    ultimo = S2220Exame.query.order_by(S2220Exame.id.desc()).first()
    if ultimo:
        print(f"ID: {ultimo.id}, Descrição: {ultimo.descricao_atividade}")
    else:
        print("Nenhum exame encontrado")