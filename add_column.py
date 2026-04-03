from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sst.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo Funcionario
class Funcionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    cpf = db.Column(db.String(20))
    matricula_esocial = db.Column(db.String(50))  # coluna nova
    nascimento = db.Column(db.String(20))
    admissao = db.Column(db.String(20))
    funcao = db.Column(db.String(50))
    empresa_id = db.Column(db.Integer)

def setup_database():
    with app.app_context():
        # Cria todas as tabelas que ainda não existem
        db.create_all()
        print("✅ Tabelas criadas / já existentes.")

if __name__ == "__main__":
    setup_database()