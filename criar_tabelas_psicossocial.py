from main import app, db
from models import Cliente, AvaliacaoPsicossocial

with app.app_context():
    # Cria as tabelas se não existirem
    db.create_all()
    print("✅ Tabelas verificadas/criadas com sucesso!")
    
    # Lista as tabelas existentes
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("\n📋 Tabelas no banco de dados:")
    for table in inspector.get_table_names():
        print(f"  - {table}")
