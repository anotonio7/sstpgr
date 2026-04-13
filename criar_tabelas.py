from main import app, db
from models import Cliente, AvaliacaoPsicossocial

with app.app_context():
    db.create_all()
    print("✅ Tabelas criadas com sucesso!")
    print(f"  - Cliente: {Cliente.__tablename__}")
    print(f"  - AvaliacaoPsicossocial: {AvaliacaoPsicossocial.__tablename__}")
