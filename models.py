from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ================= TABELA DE USUÁRIOS (LOGIN) =================
class Usuario(db.Model):
    """Tabela de usuários do sistema (autenticação)"""
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), default='cliente')  # 'admin' ou 'cliente'
    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_expira = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Usuario {self.email}>'


# ================= EMPRESA =================
# models.py - Atualize a classe Empresa
class Empresa(db.Model):
    __tablename__ = 'empresa'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20), nullable=False, unique=True)
    cep = db.Column(db.String(10))
    rua = db.Column(db.String(150))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))

    # Chave estrangeira para o usuário (cliente)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Relacionamentos
    funcionarios = db.relationship('Funcionario', backref='empresa', cascade='all, delete-orphan')
    certificado = db.relationship('ConfigCertificado', back_populates='empresa', uselist=False,
                                  cascade='all, delete-orphan')

    # Relacionamento com usuário
    usuario = db.relationship('Usuario', backref='empresas')

# ================= FUNCIONÁRIO =================
class Funcionario(db.Model):
    __tablename__ = 'funcionario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(20), nullable=False, unique=True)
    matricula_esocial = db.Column(db.String(50), nullable=False)
    cbo = db.Column(db.String(6), nullable=False)
    nascimento = db.Column(db.String(10))  # Mudar de db.Date para db.String
    admissao = db.Column(db.String(10))  # Mudar de db.Date para db.String
    funcao = db.Column(db.String(100))
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'))

    # Relacionamentos com eventos (cada um com nome único)
    s2220_events = db.relationship('EventoS2220', back_populates='funcionario', cascade='all, delete-orphan')
    s2221_events = db.relationship('EventoS2221', back_populates='funcionario', cascade='all, delete-orphan')
    s2210_events = db.relationship('EventoS2210', back_populates='funcionario', cascade='all, delete-orphan')
    s2240_events = db.relationship('EventoS2240', back_populates='funcionario', cascade='all, delete-orphan')


# ================= CONFIGURAÇÃO DO CERTIFICADO =================
# models.py - ConfigCertificado já está correto
class ConfigCertificado(db.Model):
    __tablename__ = 'config_certificado'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    certificado_pfx = db.Column(db.String(200))
    senha = db.Column(db.String(100))
    ambiente = db.Column(db.String(1), default='2')
    data_config = db.Column(db.DateTime, default=datetime.utcnow)

    empresa = db.relationship('Empresa', back_populates='certificado')
    usuario = db.relationship('Usuario', backref='certificados')


# ================= EVENTO S-2220 (ASO) =================
class EventoS2220(db.Model):
    __tablename__ = 'evento_s2220'
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_aso = db.Column(db.Date)
    crm_medico = db.Column(db.String(20))
    uf_crm = db.Column(db.String(2))
    cpf_medico = db.Column(db.String(14), nullable=True)  # CPF opcional
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

    exames = db.relationship('S2220Exame', backref='evento', cascade='all, delete-orphan')
    funcionario = db.relationship('Funcionario', back_populates='s2220_events')


class S2220Exame(db.Model):
    __tablename__ = 's2220_exame'
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento_s2220.id'), nullable=False)
    data_exame = db.Column(db.Date, nullable=False)
    tipo_exame = db.Column(db.String(50), nullable=False)
    resultado = db.Column(db.Text, nullable=False)


# ================= EVENTO S-2221 (EXAME TOXICOLÓGICO) =================
class EventoS2221(db.Model):
    __tablename__ = 'evento_s2221'
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_exame = db.Column(db.Date, nullable=False)
    tipo_exame = db.Column(db.String(50), nullable=False)
    resultado = db.Column(db.Text, nullable=False)
    laboratorio = db.Column(db.String(100))
    cpf_responsavel = db.Column(db.String(14), nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

    funcionario = db.relationship('Funcionario', back_populates='s2221_events')


# ================= EVENTO S-2210 (CAT) =================
class EventoS2210(db.Model):
    __tablename__ = 'evento_s2210'
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_acidente = db.Column(db.Date, nullable=False)
    hora_acidente = db.Column(db.Time, nullable=False)
    tipo_cat = db.Column(db.String(1), nullable=False)
    tipo_acidente = db.Column(db.String(1), nullable=False)
    local = db.Column(db.String(200), nullable=False)
    parte_atingida = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    cpf_responsavel = db.Column(db.String(14), nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

    funcionario = db.relationship('Funcionario', back_populates='s2210_events')


# ================= EVENTO S-2240 (RISCOS AMBIENTAIS) =================
class EventoS2240(db.Model):
    __tablename__ = 'evento_s2240'
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data_avaliacao = db.Column(db.Date, nullable=False)
    cpf_avaliador = db.Column(db.String(14), nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    xml_enviado = db.Column(db.Text)
    recibo = db.Column(db.Text)

    riscos = db.relationship('RiscoS2240', backref='evento', cascade='all, delete-orphan')
    funcionario = db.relationship('Funcionario', back_populates='s2240_events')


class RiscoS2240(db.Model):
    __tablename__ = 'risco_s2240'
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey('evento_s2240.id'), nullable=False)
    codigo_agente = db.Column(db.String(20), nullable=False)
    intensidade = db.Column(db.String(100))
    epi_utilizado = db.Column(db.String(200))


# ================= RECIBO DE ENVIO =================
class ReciboEnvio(db.Model):
    __tablename__ = 'recibo_envio'
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, nullable=False)
    evento_tipo = db.Column(db.String(10))  # s2220, s2221, s2210, s2240
    nome_xml = db.Column(db.String(200))
    recibo = db.Column(db.Text)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))  # enviado, erro, processado
    mensagem_erro = db.Column(db.Text)


# ================= CONFIGURAÇÃO DO SISTEMA =================
class ConfigSistema(db.Model):
    __tablename__ = 'config_sistema'
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.String(10), nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModeloDocumento(db.Model):
    __tablename__ = 'modelos_documentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.String(500))
    tipo = db.Column(db.String(20), nullable=False)  # 'pdf', 'word', 'ambos'
    categoria = db.Column(db.String(50))  # 'aso', 'cat', 'ppra', 'pcMSO', 'outro'
    arquivo_path = db.Column(db.String(500), nullable=False)
    arquivo_word_path = db.Column(db.String(500))
    versao = db.Column(db.String(20), default='1.0')
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por = db.Column(db.Integer)
    campos_variaveis = db.Column(db.Text)  # ADICIONE ESTA LINHA

    def __repr__(self):
        return f'<ModeloDocumento {self.nome}>'


# Adicione ao models.py
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    empresa = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # NÃO adicione 'avaliacoes' aqui, pois já está no outro modelo


class AvaliacaoPsicossocial(db.Model):
    __tablename__ = 'avaliacoes_psicossociais'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, nullable=False)  # Sem ForeignKey por enquanto
    nome_funcionario = db.Column(db.String(200), nullable=False)
    email_funcionario = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(100))
    setor = db.Column(db.String(100))
    token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pendente')
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    data_resposta = db.Column(db.DateTime, nullable=True)
    respostas = db.Column(db.Text, nullable=True)

    # Remova ou comente a linha abaixo:
    # cliente = db.relationship('Cliente', backref='avaliacoes')
class EPIEntrega(db.Model):
    __tablename__ = 'epi_entregas'
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    epi_nome = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    data_entrega = db.Column(db.Date, nullable=False)
    data_validade = db.Column(db.Date, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    funcionario = db.relationship('Funcionario', backref='epi_entregas')