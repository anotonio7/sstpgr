from main import app, db
from models import ReciboEnvio

with app.app_context():
    columns = [c.name for c in ReciboEnvio.__table__.columns]
    print("Campos da tabela ReciboEnvio:")
    for col in columns:
        print(f"  - {col}")
