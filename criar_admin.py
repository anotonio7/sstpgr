from main import app, db
from models import Usuario
import hashlib

with app.app_context():
    # Listar todos os usuários
    print("=== USUÁRIOS EXISTENTES ===")
    usuarios = Usuario.query.all()
    for u in usuarios:
        print(f"Email: {u.email} - Tipo: {u.tipo} - Nome: {u.nome}")
    
    print("\n=== CRIANDO ADMIN ===")
    
    # Verificar se admin já existe
    admin = Usuario.query.filter_by(email='admin@admin.com').first()
    if admin:
        print(f"Admin já existe: {admin.email}")
        admin.tipo = 'admin'
        db.session.commit()
        print(f"Usuário {admin.email} agora é ADMIN!")
    else:
        # Criar novo admin
        senha_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        novo_admin = Usuario(
            email='admin@admin.com',
            senha=senha_hash,
            nome='Administrador Master',
            tipo='admin'
        )
        db.session.add(novo_admin)
        db.session.commit()
        print("Admin criado: admin@admin.com / admin123")
    
    # Verificar resultado
    print("\n=== RESULTADO FINAL ===")
    admin_final = Usuario.query.filter_by(email='admin@admin.com').first()
    if admin_final:
        print(f"Email: {admin_final.email} - Tipo: {admin_final.tipo}")