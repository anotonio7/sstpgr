from main import app, db
from models import *

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Banco de dados recriado com sucesso!")