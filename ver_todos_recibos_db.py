from main import app, db
from models import ReciboEnvio

with app.app_context():
    recibos = ReciboEnvio.query.order_by(ReciboEnvio.id.desc()).all()
    print(f"\n=== TODOS OS RECIBOS ({len(recibos)}) ===\n")
    for r in recibos:
        print(f"ID: {r.id}")
        print(f"  Tipo: {r.evento_tipo}")
        print(f"  Status: {r.status}")
        print(f"  Data: {r.data_envio}")
        print(f"  Recibo: {r.recibo[:50] if r.recibo else 'N/A'}")
        print(f"  XML: {r.nome_xml}")
        print("-" * 50)
