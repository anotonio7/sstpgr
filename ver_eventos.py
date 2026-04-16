from main import app, db
from models import EventoS2240

with app.app_context():
    eventos = EventoS2240.query.filter_by(status="pendente").all()
    print(f"Eventos pendentes: {len(eventos)}")
    for e in eventos:
        print(f"ID: {e.id} - Funcionário: {e.funcionario_id}")
