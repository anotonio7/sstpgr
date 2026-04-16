from main import app, db
from models import Cliente, AvaliacaoPsicossocial

with app.app_context():
    db.create_all()
    print("? Tabelas atualizadas com sucesso!")
    
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("\n?? Tabelas no banco de dados:")
    for table in inspector.get_table_names():
        print(f"  - {table}")
