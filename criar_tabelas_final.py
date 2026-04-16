import os
import sys

# Adiciona o diret?rio atual
sys.path.insert(0, os.getcwd())

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Cria app Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/sst.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo Cliente
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    empresa = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

# Modelo AvaliacaoPsicossocial
class AvaliacaoPsicossocial(db.Model):
    __tablename__ = 'avaliacoes_psicossociais'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    funcionario_id = db.Column(db.Integer)
    token = db.Column(db.String(100), unique=True, nullable=False)
    email_enviado = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.DateTime)
    data_resposta = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pendente')
    respostas = db.Column(db.Text)
    nome_funcionario = db.Column(db.String(200))
    cargo = db.Column(db.String(200))
    setor = db.Column(db.String(200))
    pontuacao_total = db.Column(db.Integer)
    nivel_risco = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

print("Criando tabelas...")

with app.app_context():
    db.create_all()
    print("? Tabelas criadas/verificadas com sucesso!")
    
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("\n?? Todas as tabelas no banco de dados:")
    for table in inspector.get_table_names():
        print(f"  - {table}")
