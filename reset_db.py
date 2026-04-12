# reset_db.py
from main import app, db
from models import *
from werkzeug.security import generate_password_hash

with app.app_context():
    print("Recriando banco de dados...")
    db.drop_all()
    db.create_all()
    print("✅ Banco de dados recriado com sucesso!")

    # Criar usuário admin
    admin = Usuario(
        nome="Administrador",
        email="admin@admin.com",
        senha=generate_password_hash("admin123"),
        tipo="admin"
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Usuário admin criado: admin@admin.com / admin123")

    print("\nBanco de dados pronto para uso!")