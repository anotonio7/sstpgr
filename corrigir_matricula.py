from main import app, db
from models import Funcionario

print("Corrigindo matrículas...")

with app.app_context():
    for f in Funcionario.query.all():
        if not f.matricula_esocial:
            f.matricula_esocial = f"MAT{f.id:05d}"

    db.session.commit()

print("Matrículas corrigidas com sucesso!")