from main import app, db
from models import ReciboEnvio

with app.app_context():
    recibos = ReciboEnvio.query.all()
    print(f"Total de recibos: {len(recibos)}")
    for r in recibos:
        print(f"ID: {r.id} | Tipo: {r.evento_tipo} | Status: {r.status} | Recibo: {r.recibo[:50] if r.recibo else 'N/A'}")
