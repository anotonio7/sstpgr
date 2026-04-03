from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Empresa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False, unique=True)
    cep = db.Column(db.String(10))
    rua = db.Column(db.String(150))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    funcionarios = db.relationship('Funcionario', backref='empresa', cascade='all, delete-orphan')

class Funcionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(20), nullable=False, unique=True)
    matricula_esocial = db.Column(db.String(50))   # matrícula do eSocial
    nascimento = db.Column(db.Date)
    admissao = db.Column(db.Date)
    funcao = db.Column(db.String(100))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))
    # Relacionamentos com eventos
    s2220_events = db.relationship('EventoS2220', backref='funcionario', cascade='all, delete-orphan')
    s2221_events = db.relationship('EventoS2221', backref='funcionario', cascade='all, delete-orphan')
    s2210_events = db.relationship('EventoS2210', backref='funcionario', cascade='all, delete-orphan')
    s2240_events = db.relationship('EventoS2240', backref='funcionario', cascade='all, delete-orphan')

# Evento S-2220 - Monitoramento da Saúde
class EventoS2220(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_aso = db.Column(db.Date)   # data do ASO
    crm_medico = db.Column(db.String(20))
    uf_crm = db.Column(db.String(2))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

    # Relacionamento com os exames
    exames = db.relationship('S2220Exame', backref='evento', cascade='all, delete-orphan')

class S2220Exame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento_s2220.id'), nullable=False)
    data_exame = db.Column(db.Date, nullable=False)
    tipo_exame = db.Column(db.String(50), nullable=False)
    resultado = db.Column(db.Text, nullable=False)
# Evento S-2221 - Exame Toxicológico
class EventoS2221(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_exame = db.Column(db.Date, nullable=False)
    tipo_exame = db.Column(db.String(50), nullable=False)
    resultado = db.Column(db.Text, nullable=False)
    laboratorio = db.Column(db.String(100))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

# Evento S-2210 - CAT
class EventoS2210(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_acidente = db.Column(db.Date, nullable=False)
    tipo_acidente = db.Column(db.String(50), nullable=False)  # típico, trajeto, etc.
    local = db.Column(db.String(200))
    parte_atingida = db.Column(db.String(100))
    descricao = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

# Evento S-2240 - Condições Ambientais
class EventoS2240(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_avaliacao = db.Column(db.Date, nullable=False)
    agente_risco = db.Column(db.String(100), nullable=False)
    intensidade = db.Column(db.String(50))
    epi_utilizado = db.Column(db.String(200))
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

# Configuração do certificado
class ConfigCertificado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    certificado_pfx = db.Column(db.String(200))   # caminho do arquivo .pfx
    senha = db.Column(db.String(200))             # senha do certificado
    ambiente = db.Column(db.String(1), default='2')  # 1=produção, 2=homologação