# ================= IMPORTAÇÕES PADRÃO =================
import os
import re
import json
import secrets
import hashlib
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from functools import wraps

# ================= IMPORTAÇÕES FLASK =================
from flask import Flask, send_file, session, request, flash, redirect, url_for, render_template, Response, make_response

# ================= IMPORTAÇÕES FLASK-LOGIN =================
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user

# ================= IMPORTAÇÕES SQLALCHEMY =================
from sqlalchemy.exc import IntegrityError

# ================= IMPORTAÇÕES WERKZEUG =================
from werkzeug.utils import secure_filename

# ================= IMPORTAÇÕES REPORTLAB =================
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
# Topo do arquivo main.py
from datetime import datetime  # ← Se tiver aqui, não precisa dentro da função
# ================= IMPORTAÇÕES DOCX =================
from docx import Document
from docx.shared import Inches
from models import Cliente, AvaliacaoPsicossocial
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import hashlib
import secrets
from flask_mail import Mail, Message  # ← ADICIONE ESTA LINHA
from models import EPIEntrega, Funcionario  # junto com seus outros modelos
# ... resto das importações
# ================= IMPORTAÇÕES DOS MODELOS =================
from models import (
    db,
    Usuario,
    Empresa,
    Funcionario,
    EventoS2220,
    S2220Exame,
    EventoS2221,
    EventoS2210,
    EventoS2240,
    RiscoS2240,
    ConfigCertificado,
    ConfigSistema,
    ModeloDocumento,
    ReciboEnvio
)

# ================= IMPORTAÇÕES UTILITÁRIOS =================
from esocial_utils import (
    carregar_certificado,
    assinar_xml,
    gerar_xml_s2220,
    gerar_xml_s2221,
    gerar_xml_s2210,
    gerar_xml_s2240,
    enviar_lote
)

# ================= INICIALIZAÇÃO DO FLASK =================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/sst2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configuração do domínio para links externos
# Inicializar banco de dados
db.init_app(app)

# ================= CONFIGURAÇÃO DO LOGIN =================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

# ================= FUNÇÕES AUXILIARES =================
def validar_cpf(cpf):
    """Valida CPF"""
    if not cpf:
        return False
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11:
        return False
    return True

# ================= FUNÇÃO PARA GERAR PDF DO S-2220 =================
def gerar_pdf_s2220(evento):
    """Gera PDF do ASO (S-2220) - Com assinatura do funcionário"""
    # Coloque aqui a função completa que criamos anteriormente
    # ... (código completo da função gerar_pdf_s2220)
    pass  # Substitua pelo código completo

# ================= ROTAS DO SISTEMA =================
# Suas rotas aqui...
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-mude-em-producao-123456'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sst2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'certs')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Configuração de email (para recuperação de senha)
# Configuração de email (para recuperação de senha)
# Configuração de email (para recuperação de senha)
# ==================== CONFIGURAÇÃO DE EMAIL ====================
# ==================== CONFIGURAÇÃO DE EMAIL ====================
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'meusistema@gmail.com',  # Altere para seu email
    'senha': 'abcd efgh ijkl mnop'  # Senha de app de 16 caracteres
}

app.config['MAIL_SERVER'] = EMAIL_CONFIG['smtp_server']
app.config['MAIL_PORT'] = EMAIL_CONFIG['smtp_port']
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_CONFIG['email']
app.config['MAIL_PASSWORD'] = EMAIL_CONFIG['senha']
app.config['MAIL_DEFAULT_SENDER'] = EMAIL_CONFIG['email']

mail = Mail(app)  # Agora o 'Mail' está definido


def enviar_email_avaliacao(cliente, avaliacao):
    link = url_for('responder_avaliacao', token=avaliacao.token, _external=True)

    # MODO TESTE - Só exibe no console
    print("\n" + "=" * 60)
    print("🔵 MODO TESTE - Email não enviado")
    print("=" * 60)
    print(f"Para: {cliente.email}")
    print(f"Assunto: Avaliação Psicossocial - {avaliacao.nome_funcionario}")
    print(f"\n🔗 LINK DE ACESSO:")
    print(f"{link}")
    print("=" * 60 + "\n")

    # Simula envio
    avaliacao.email_enviado = True
    avaliacao.data_envio = datetime.now()
    db.session.commit()

    return True
# ================= LOGIN MANAGER =================
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, email, nome, tipo):
        self.id = id
        self.email = email
        self.nome = nome
        self.tipo = tipo


@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('instance/sst2.db')
    c = conn.cursor()
    c.execute("SELECT id, email, nome, tipo FROM usuarios WHERE id = ?", (user_id,))
    usuario = c.fetchone()
    conn.close()
    if usuario:
        return User(usuario[0], usuario[1], usuario[2], usuario[3])
    return None


# ================= DECORATORS =================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash('Acesso restrito a administradores', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


# ================= FUNÇÕES DE USUÁRIO =================
def init_db():
    conn = sqlite3.connect('instance/sst2.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        nome TEXT,
        tipo TEXT DEFAULT 'cliente',
        reset_token TEXT,
        reset_token_expira TEXT
    )''')

    # Criar admin padrão se não existir
    c.execute("SELECT * FROM usuarios WHERE email = 'admin@admin.com'")
    if not c.fetchone():
        senha_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO usuarios (email, senha, nome, tipo) VALUES (?, ?, ?, ?)",
                  ('admin@admin.com', senha_hash, 'Administrador', 'admin'))

    conn.commit()
    conn.close()


def enviar_email_recuperacao(email_destino, token):
    link_recuperacao = f"http://localhost:5000/redefinir-senha/{token}"

    # Exibe o link diretamente para o usuário
    flash('=' * 50, 'info')
    flash('🔐 RECUPERAÇÃO DE SENHA - MODO DESENVOLVIMENTO', 'info')
    flash(f'📧 Seria enviado para: {email_destino}', 'info')
    flash(f'🔗 LINK PARA REDEFINIR SENHA:', 'info')
    flash(f'{link_recuperacao}', 'success')
    flash('⚠️ Copie e cole este link no navegador', 'warning')
    flash('=' * 50, 'info')

    # Log no console
    print(f"\n{'=' * 60}")
    print(f"EMAIL DE RECUPERAÇÃO (MODO DEBUG)")
    print(f"Para: {email_destino}")
    print(f"Link: {link_recuperacao}")
    print(f"{'=' * 60}\n")

    return True

# ================= ROTAS DE AUTENTICAÇÃO =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()

        conn = sqlite3.connect('instance/sst2.db')
        c = conn.cursor()
        c.execute("SELECT id, email, nome, tipo FROM usuarios WHERE email = ? AND senha = ?",
                  (email, senha_hash))
        usuario = c.fetchone()
        conn.close()

        if usuario:
            user = User(usuario[0], usuario[1], usuario[2], usuario[3])
            login_user(user)
            flash(f'Bem-vindo, {usuario[2]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos', 'danger')

    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        nome = request.form['nome']

        # Validações
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('Email inválido', 'danger')
            return redirect(url_for('registro'))

        if len(senha) < 6:
            flash('Senha deve ter pelo menos 6 caracteres', 'danger')
            return redirect(url_for('registro'))

        senha_hash = hashlib.sha256(senha.encode()).hexdigest()

        conn = sqlite3.connect('instance/sst2.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO usuarios (email, senha, nome, tipo) VALUES (?, ?, ?, 'cliente')",
                      (email, senha_hash, nome))
            conn.commit()
            flash('Cadastro realizado! Faça login', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email já cadastrado', 'danger')
        finally:
            conn.close()

    return render_template('registro.html')


@app.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        email = request.form['email']

        conn = sqlite3.connect('instance/sst2.db')
        c = conn.cursor()
        c.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        usuario = c.fetchone()

        if usuario:
            token = secrets.token_urlsafe(32)
            c.execute(
                "UPDATE usuarios SET reset_token = ?, reset_token_expira = datetime('now', '+1 hour') WHERE id = ?",
                (token, usuario[0]))
            conn.commit()

            if enviar_email_recuperacao(email, token):
                flash('Email de recuperação enviado! Verifique sua caixa de entrada', 'success')
            else:
                flash('Erro ao enviar email. Tente novamente.', 'danger')
        else:
            flash('Email não encontrado', 'warning')

        conn.close()

    return render_template('recuperar_senha.html')


@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    conn = sqlite3.connect('instance/sst2.db')
    c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE reset_token = ? AND reset_token_expira > datetime('now')", (token,))
    usuario = c.fetchone()

    if not usuario:
        flash('Link inválido ou expirado', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']

        if len(nova_senha) < 6:
            flash('Senha deve ter pelo menos 6 caracteres', 'danger')
        elif nova_senha != confirmar_senha:
            flash('Senhas não conferem', 'danger')
        else:
            senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
            c.execute("UPDATE usuarios SET senha = ?, reset_token = NULL, reset_token_expira = NULL WHERE id = ?",
                      (senha_hash, usuario[0]))
            conn.commit()
            flash('Senha redefinida com sucesso! Faça login', 'success')
            return redirect(url_for('login'))

    conn.close()
    return render_template('redefinir_senha.html', token=token)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado', 'info')
    return redirect(url_for('login'))


# ================= DASHBOARD PRINCIPAL =================
@app.route('/')
@login_required
def dashboard():
    empresas = Empresa.query.count()
    funcionarios = Funcionario.query.count()
    s2220 = EventoS2220.query.count()
    s2221 = EventoS2221.query.count()
    s2210 = EventoS2210.query.count()
    s2240 = EventoS2240.query.count()

    if current_user.tipo == 'admin':
        return render_template('admin_dashboard.html',
                               empresas=empresas,
                               funcionarios=funcionarios,
                               s2220=s2220, s2221=s2221, s2210=s2210, s2240=s2240,
                               empresas_lista=Empresa.query.order_by(Empresa.id.desc()).limit(5).all(),
                               funcionarios_lista=Funcionario.query.order_by(Funcionario.id.desc()).limit(5).all()
                               )
    else:
        return render_template('cliente_dashboard.html',
                               empresas=empresas,
                               funcionarios=funcionarios,
                               s2220=s2220, s2221=s2221, s2210=s2210, s2240=s2240
                               )


# ================= ADMIN: GESTÃO DE USUÁRIOS =================
@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    conn = sqlite3.connect('instance/sst2.db')
    c = conn.cursor()
    c.execute("SELECT id, email, nome, tipo FROM usuarios ORDER BY id")
    usuarios = c.fetchall()
    conn.close()
    return render_template('admin_usuarios.html', usuarios=usuarios)


@app.route('/admin/usuario/<int:usuario_id>/excluir')
@admin_required
def admin_excluir_usuario(usuario_id):
    if usuario_id == current_user.id:
        flash('Não pode excluir a si mesmo', 'danger')
        return redirect(url_for('admin_usuarios'))

    conn = sqlite3.connect('instance/sst2.db')
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    flash('Usuário excluído com sucesso', 'success')
    return redirect(url_for('admin_usuarios'))


@app.route('/admin/usuario/<int:usuario_id>/tornar-admin')
@admin_required
def admin_tornar_admin(usuario_id):
    conn = sqlite3.connect('instance/sst2.db')
    c = conn.cursor()
    c.execute("UPDATE usuarios SET tipo = 'admin' WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    flash('Usuário promovido a administrador', 'success')
    return redirect(url_for('admin_usuarios'))


@app.route('/admin/usuario/<int:usuario_id>/tornar-cliente')
@admin_required
def admin_tornar_cliente(usuario_id):
    if usuario_id == current_user.id:
        flash('Não pode rebaixar a si mesmo', 'danger')
        return redirect(url_for('admin_usuarios'))

    conn = sqlite3.connect('instance/sst2.db')
    c = conn.cursor()
    c.execute("UPDATE usuarios SET tipo = 'cliente' WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    flash('Usuário rebaixado para cliente', 'success')
    return redirect(url_for('admin_usuarios'))


# ================= FUNÇÃO CEP =================
def buscar_endereco_por_cep(cep):
    import requests
    cep = cep.replace("-", "").strip()
    url = f"https://viacep.com.br/ws/{cep}/json/"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        if "erro" not in data:
            return {
                "rua": data.get("logradouro", ""),
                "bairro": data.get("bairro", ""),
                "cidade": data.get("localidade", ""),
                "estado": data.get("uf", "")
            }
    return None


# ================= ROTAS EMPRESA =================
@app.route('/empresa/list')
@login_required
def list_empresas():
    empresas = Empresa.query.all()
    return render_template('empresa/list.html', empresas=empresas)


@app.route('/empresa/create', methods=['GET', 'POST'])
@login_required
def create_empresa():
    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form['cnpj']
        cep = request.form['cep']

        # Verificar se CNPJ já existe
        empresa_existente = Empresa.query.filter_by(cnpj=cnpj).first()
        if empresa_existente:
            flash(f'Erro: CNPJ {cnpj} já está cadastrado para a empresa {empresa_existente.nome}', 'danger')
            return redirect(url_for('create_empresa'))

        endereco = buscar_endereco_por_cep(cep) if cep else None
        e = Empresa(
            nome=nome,
            cnpj=cnpj,
            cep=cep,
            rua=endereco.get('rua') if endereco else '',
            bairro=endereco.get('bairro') if endereco else '',
            cidade=endereco.get('cidade') if endereco else '',
            estado=endereco.get('estado') if endereco else '',
            usuario_id=current_user.id  # VÍRGULA ADICIONADA AQUI
        )
        db.session.add(e)
        try:
            db.session.commit()
            flash('Empresa criada com sucesso!', 'success')
            return redirect(url_for('list_empresas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar empresa: {str(e)}', 'danger')
            return redirect(url_for('create_empresa'))

    return render_template('empresa/create.html')


@app.route('/empresa/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_empresa(id):
    e = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        e.nome = request.form['nome']
        e.cnpj = request.form['cnpj']
        e.cep = request.form['cep']
        endereco = buscar_endereco_por_cep(e.cep) if e.cep else None
        if endereco:
            e.rua = endereco['rua']
            e.bairro = endereco['bairro']
            e.cidade = endereco['cidade']
            e.estado = endereco['estado']
        db.session.commit()
        flash('Empresa atualizada!')
        return redirect(url_for('list_empresas'))
    return render_template('empresa/edit.html', e=e)


@app.route('/empresa/delete/<int:id>')
@login_required
def delete_empresa(id):
    e = Empresa.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    flash('Empresa excluída!')
    return redirect(url_for('list_empresas'))


# ================= ROTAS FUNCIONARIO =================
@app.route('/funcionario/list')
@login_required
def list_funcionarios():
    funcionarios = Funcionario.query.all()
    return render_template('funcionario/list.html', funcionarios=funcionarios)





# Depois, substitua toda a rota:

@app.route('/funcionario/create', methods=['GET', 'POST'])
@login_required
def create_funcionario():
    if request.method == 'POST':
        try:
            # Converter strings de data para objetos date
            nascimento = datetime.strptime(request.form['nascimento'], '%Y-%m-%d').date()
            admissao = datetime.strptime(request.form['admissao'], '%Y-%m-%d').date()

            # Criar novo funcionário com datas convertidas
            funcionario = Funcionario(
                nome=request.form['nome'],
                cpf=request.form['cpf'],
                matricula_esocial=request.form.get('matricula_esocial', ''),
                cbo=request.form['cbo'],
                nascimento=nascimento,  # Agora é objeto date
                admissao=admissao,  # Agora é objeto date
                funcao=request.form['funcao'],
                empresa_id=int(request.form['empresa_id'])
            )

            db.session.add(funcionario)
            db.session.commit()

            flash('Funcionário cadastrado com sucesso!', 'success')
            return redirect(url_for('list_funcionarios'))

        except IntegrityError:
            db.session.rollback()
            flash('Erro: CPF já cadastrado no sistema!', 'error')
            return redirect(url_for('create_funcionario'))

        except ValueError as e:
            db.session.rollback()
            flash(f'Erro no formato das datas: {str(e)}', 'error')
            return redirect(url_for('create_funcionario'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar funcionário: {str(e)}', 'error')
            return redirect(url_for('create_funcionario'))

    # GET request - mostrar formulário
    empresas = Empresa.query.all()
    return render_template('funcionario/create.html', empresas=empresas)


@app.route('/funcionario/edit/<int:id>', methods=['GET', 'POST'])  # <-- IMPORTANTE: tem que ter GET e POST
def edit_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)

    if request.method == 'POST':
        # Processar o formulário (atualizar)
        funcionario.nome = request.form['nome']
        funcionario.cpf = request.form['cpf']
        funcionario.matricula_esocial = request.form.get('matricula_esocial')
        funcionario.cbo = request.form['cbo']
        funcionario.funcao = request.form['funcao']
        funcionario.empresa_id = request.form['empresa_id']

        db.session.commit()
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('list_funcionarios'))

    # Se for GET, mostrar o formulário
    empresas = Empresa.query.all()
    return render_template('funcionario/edit.html', funcionario=funcionario, empresas=empresas)


@app.route('/funcionario/delete/<int:id>', methods=['POST'])
def delete_funcionario(id):
    # lógica de exclusão
    funcionario = Funcionario.query.get_or_404(id)
    db.session.delete(funcionario)
    db.session.commit()
    flash('Funcionário excluído com sucesso!', 'success')
    return redirect(url_for('list_funcionarios'))

@app.route('/funcionario/create', methods=['GET'])
def create_funcionario_form():
    empresas = Empresa.query.all()
    return render_template('funcionario_create.html', empresas=empresas)




# main.py
@app.route('/enviar_evento/<int:funcionario_id>')
@login_required
def enviar_evento(funcionario_id):
    funcionario = Funcionario.query.get_or_404(funcionario_id)

    # Verificar se o funcionário pertence a uma empresa do cliente
    if current_user.tipo != 'admin':
        empresa = Empresa.query.filter_by(
            id=funcionario.empresa_id,
            usuario_id=current_user.id
        ).first()

        if not empresa:
            flash('Sem permissão para este funcionário.', 'danger')
            return redirect(url_for('dashboard'))
    else:
        empresa = Empresa.query.get(funcionario.empresa_id)

    # Buscar o certificado da empresa
    certificado = ConfigCertificado.query.filter_by(empresa_id=empresa.id).first()

    if not certificado:
        flash(f'Empresa {empresa.nome} não possui certificado configurado.', 'warning')
        return redirect(url_for('dashboard'))

    # Usar o certificado para enviar ao eSocial
    # ... código de envio usando o certificado da empresa

    return render_template('enviar_evento.html',
                           funcionario=funcionario,
                           empresa=empresa,
                           certificado=certificado)


# ================= FUNÇÃO DE VALIDAÇÃO DE CPF =================
def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    return resto == int(cpf[10])


# ================= FUNÇÃO PARA GERAR PDF DO S-2220 =================



def gerar_pdf_s2220(evento):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f"ASO_{evento.funcionario.nome}_{evento.id}"
    )
    styles = getSampleStyleSheet()

    cor_cinza_claro = colors.HexColor('#f5f5f5')
    cor_cinza_medio = colors.HexColor('#e0e0e0')
    cor_cinza_escuro = colors.HexColor('#333333')
    cor_borda = colors.HexColor('#999999')
    cor_titulo = colors.HexColor('#2c3e50')

    style_titulo_principal = ParagraphStyle(
        name='TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=cor_titulo,
        alignment=1,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    style_subtitulo = ParagraphStyle(
        name='Subtitulo',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=cor_titulo,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    style_normal = ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=cor_cinza_escuro
    )
    style_assinatura = ParagraphStyle(
        name='Assinatura',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=cor_cinza_escuro,
        alignment=1
    )

    def add_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(cor_cinza_escuro)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 10, "eSocial - Monitoramento da Saúde (S-2220)")
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin - 10,
                               f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.setStrokeColor(cor_borda)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - 15, doc.width + doc.leftMargin,
                    doc.height + doc.topMargin - 15)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 10, f"Documento gerado eletronicamente - ID: {evento.id}")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 10, f"Página {doc.page}")
        canvas.restoreState()

    story = []
    story.append(Paragraph("Evento S-2220 – Monitoramento da Saúde (ASO)", style_titulo_principal))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Dados do Funcionário", style_subtitulo))
    func = evento.funcionario
    dados_func = [
        ["Nome:", func.nome],
        ["CPF:", func.cpf],
        ["Matrícula eSocial:", func.matricula_esocial],
        ["CBO:", func.cbo],
        ["Nascimento:", func.nascimento.strftime('%d/%m/%Y') if func.nascimento else ""],
        ["Admissão:", func.admissao.strftime('%d/%m/%Y') if func.admissao else ""],
        ["Função/Cargo:", func.funcao],
    ]
    t_func = Table(dados_func, colWidths=[4 * cm, 12 * cm])
    t_func.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BACKGROUND', (0, 0), (0, -1), cor_cinza_claro),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), cor_cinza_escuro),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_func)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Dados do ASO", style_subtitulo))
    dados_aso = [
        ["Data do ASO:", evento.data_aso.strftime('%d/%m/%Y')],
        ["CRM Médico:", evento.crm_medico],
        ["UF CRM:", evento.uf_crm],
        ["CPF Médico:", evento.cpf_medico],
    ]
    t_aso = Table(dados_aso, colWidths=[4 * cm, 12 * cm])
    t_aso.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BACKGROUND', (0, 0), (0, -1), cor_cinza_claro),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_aso)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Exames Realizados", style_subtitulo))
    if evento.exames:
        exames_data = [["Data", "Tipo de Exame", "Resultado"]]
        for ex in evento.exames:
            exames_data.append([
                ex.data_exame.strftime('%d/%m/%Y'),
                ex.tipo_exame,
                ex.resultado
            ])
        t_exames = Table(exames_data, colWidths=[3 * cm, 5 * cm, 8 * cm])
        t_exames.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
            ('BACKGROUND', (0, 0), (-1, 0), cor_cinza_medio),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), cor_cinza_escuro),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t_exames)
    else:
        story.append(Paragraph("Nenhum exame registrado.", style_normal))

    story.append(Spacer(1, 24))
    story.append(Paragraph("Declaro que recebi o ASO e estou ciente dos resultados.", style_normal))
    story.append(Spacer(1, 12))
    assinatura_flowable = Paragraph(
        "_________________________________________",
        ParagraphStyle('AssinaturaLinha', parent=style_assinatura, alignment=1, fontSize=10, textColor=colors.black)
    )
    story.append(assinatura_flowable)
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"{func.nome} - {func.cpf}", style_assinatura))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Assinatura do Funcionário (ou representante legal)", style_assinatura))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Data: ___/___/______", style_assinatura))
    story.append(Spacer(1, 16))
    story.append(Paragraph("_________________________________________", style_assinatura))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Médico: {evento.crm_medico} - {evento.uf_crm}", style_assinatura))
    story.append(Paragraph("Assinatura do Médico Responsável", style_assinatura))

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer


# ================= ROTAS S-2220 =================
@app.route('/s2220/list')
@login_required
def list_s2220():
    eventos = EventoS2220.query.all()
    return render_template('eventos/s2220_list.html', eventos=eventos)


@app.route('/s2220/create', methods=['GET', 'POST'])
@login_required
def create_s2220():
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        funcionario_id = request.form.get('funcionario_id')
        data_aso = request.form.get('data_aso')
        crm_medico = request.form.get('crm_medico')
        uf_crm = request.form.get('uf_crm')
        cpf_medico = request.form.get('cpf_medico')
        apenas_xml = request.form.get('apenas_xml') == 'true'
        gerar_pdf = request.form.get('gerar_pdf') == 'true'

        if not all([funcionario_id, data_aso, crm_medico, uf_crm, cpf_medico]):
            flash('Todos os campos são obrigatórios', 'danger')
            return redirect(url_for('create_s2220'))
        if not validar_cpf(cpf_medico):
            flash('CPF do médico inválido', 'danger')
            return redirect(url_for('create_s2220'))

        funcionario = db.session.get(Funcionario, int(funcionario_id))
        if not funcionario or not funcionario.matricula_esocial or not funcionario.cbo:
            flash('Funcionário inválido ou sem matrícula/CBO', 'danger')
            return redirect(url_for('create_s2220'))

        datas = request.form.getlist('data_exame[]')
        tipos = request.form.getlist('tipo_exame[]')
        resultados = request.form.getlist('resultado[]')
        exames = []
        for i in range(len(datas)):
            if datas[i] and tipos[i] and resultados[i]:
                exames.append({
                    'data_exame': datetime.strptime(datas[i], '%Y-%m-%d').date(),
                    'tipo_exame': tipos[i],
                    'resultado': resultados[i]
                })

        if apenas_xml or gerar_pdf:
            evento_temp = EventoS2220(
                funcionario_id=funcionario.id,
                data_aso=datetime.strptime(data_aso, '%Y-%m-%d').date(),
                crm_medico=crm_medico,
                uf_crm=uf_crm,
                cpf_medico=cpf_medico
            )
            for ex in exames:
                exame_temp = S2220Exame(
                    data_exame=ex['data_exame'],
                    tipo_exame=ex['tipo_exame'],
                    resultado=ex['resultado']
                )
                evento_temp.exames.append(exame_temp)

            if apenas_xml:
                empresa = funcionario.empresa
                xml_gerado = gerar_xml_s2220(evento_temp, empresa, funcionario, ambiente='2')
                buffer = BytesIO(xml_gerado.encode('utf-8'))
                return send_file(buffer, as_attachment=True, download_name='S2220.xml', mimetype='application/xml')
            elif gerar_pdf:
                pdf_buffer = gerar_pdf_s2220(evento_temp)
                return send_file(pdf_buffer, as_attachment=True, download_name='S2220.pdf', mimetype='application/pdf')

        evento = EventoS2220(
            funcionario_id=funcionario.id,
            data_aso=datetime.strptime(data_aso, '%Y-%m-%d').date(),
            crm_medico=crm_medico,
            uf_crm=uf_crm,
            cpf_medico=cpf_medico
        )
        db.session.add(evento)
        db.session.flush()
        for ex in exames:
            exame_obj = S2220Exame(
                evento_id=evento.id,
                data_exame=ex['data_exame'],
                tipo_exame=ex['tipo_exame'],
                resultado=ex['resultado']
            )
            db.session.add(exame_obj)
        db.session.commit()
        flash('Evento S-2220 criado com sucesso!', 'success')
        return redirect(url_for('list_s2220'))

    return render_template('eventos/s2220_create.html', funcionarios=funcionarios)


@app.route('/s2220/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        evento.funcionario_id = request.form.get('funcionario_id')
        evento.data_aso = datetime.strptime(request.form['data_aso'], '%Y-%m-%d').date()
        evento.crm_medico = request.form['crm_medico']
        evento.uf_crm = request.form['uf_crm']
        evento.cpf_medico = request.form['cpf_medico']
        if not validar_cpf(evento.cpf_medico):
            flash('CPF do médico inválido', 'danger')
            return redirect(url_for('edit_s2220', id=id))

        for exame in evento.exames:
            db.session.delete(exame)
        db.session.flush()

        datas = request.form.getlist('data_exame[]')
        tipos = request.form.getlist('tipo_exame[]')
        resultados = request.form.getlist('resultado[]')
        for i in range(len(datas)):
            if datas[i] and tipos[i] and resultados[i]:
                novo_exame = S2220Exame(
                    evento_id=evento.id,
                    data_exame=datetime.strptime(datas[i], '%Y-%m-%d').date(),
                    tipo_exame=tipos[i],
                    resultado=resultados[i]
                )
                db.session.add(novo_exame)
        db.session.commit()
        flash('Evento S-2220 atualizado!', 'success')
        return redirect(url_for('list_s2220'))

    return render_template('eventos/s2220_edit.html', evento=evento, funcionarios=funcionarios)


@app.route('/s2220/delete/<int:id>')
@login_required
def delete_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento S-2220 excluído!', 'success')
    return redirect(url_for('list_s2220'))


@app.route('/s2220/download_xml/<int:id>')
@login_required
def download_xml_s2220(id):
    try:
        evento = EventoS2220.query.get_or_404(id)
        funcionario = evento.funcionario
        empresa = funcionario.empresa
        xml_str = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')
        buffer = BytesIO(xml_str.encode('utf-8'))
        return send_file(buffer, as_attachment=True, download_name=f's2220_{evento.id}.xml', mimetype='application/xml')
    except Exception as e:
        flash(f'Erro ao gerar XML: {str(e)}', 'error')
        return redirect(url_for('list_s2220'))
@app.route('/s2220/view_xml/<int:id>')
@login_required
def view_xml_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    funcionario = evento.funcionario
    empresa = funcionario.empresa
    xml_str = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')
    return Response(xml_str, mimetype='application/xml')


@app.route('/s2220/send/<int:id>')
@login_required
def send_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    if evento.status != 'pendente':
        flash('Este evento já foi enviado!', 'warning')
        return redirect(url_for('list_s2220'))
    cfg = ConfigCertificado.query.first()
    if not cfg:
        flash('Configure o certificado digital antes de enviar!', 'danger')
        return redirect(url_for('config_certificado'))
    try:
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        empresa = evento.funcionario.empresa
        xml = gerar_xml_s2220(evento, empresa, evento.funcionario, cfg.ambiente)
        xml_assinado = assinar_xml(xml, cert_pem, key_pem)
        recibo = enviar_lote(xml_assinado, cfg.ambiente)
        evento.xml_enviado = xml_assinado
        evento.recibo = recibo
        evento.status = 'enviado'
        db.session.commit()
        flash('Evento enviado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao enviar: {str(e)}', 'danger')
    return redirect(url_for('list_s2220'))


@app.route('/s2220/teste_xml/<int:id>')
@login_required
def teste_xml_s2220(id):
    """Rota para testar a geração do XML e ver erros"""
    import traceback
    from io import BytesIO

    try:
        evento = db.session.get(EventoS2220, id)
        if not evento:
            return "Evento não encontrado", 404

        funcionario = evento.funcionario
        empresa = funcionario.empresa

        # Verificar dados obrigatórios
        erros = []
        if not empresa.cnpj:
            erros.append("Empresa sem CNPJ")
        if not funcionario.matricula_esocial:
            erros.append("Funcionário sem matrícula eSocial")
        if not funcionario.cpf:
            erros.append("Funcionário sem CPF")
        if not funcionario.cbo:
            erros.append("Funcionário sem CBO")
        if not evento.crm_medico:
            erros.append("Evento sem CRM médico")
        if not evento.cpf_medico:
            erros.append("Evento sem CPF do médico")

        if erros:
            return f"Erros encontrados:<br>{'<br>'.join(erros)}"

        # Tentar gerar o XML
        xml_str = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')

        if not xml_str:
            return "XML gerado está vazio"

        # Mostrar as primeiras 500 linhas do XML
        linhas = xml_str.split('\n')[:50]
        return f"""
        <h3>XML Gerado com Sucesso!</h3>
        <pre>{'<br>'.join(linhas)}</pre>
        <p>Total de caracteres: {len(xml_str)}</p>
        <a href="{url_for('download_xml_s2220', id=id)}">Clique aqui para baixar</a>
        """

    except Exception as e:
        return f"""
        <h3>Erro ao gerar XML:</h3>
        <pre>{str(e)}</pre>
        <pre>{traceback.format_exc()}</pre>
        """
########################################################## GERAR PDF PARA O ASO #############################
@app.route('/s2220/download_pdf/<int:id>')
@login_required
def download_pdf_s2220(id):
    try:
        evento = db.session.get(EventoS2220, id)
        if not evento:
            flash('Evento não encontrado', 'error')
            return redirect(url_for('list_s2220'))

        pdf_buffer = gerar_pdf_s2220(evento)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'S2220_{evento.id}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('list_s2220'))


def gerar_pdf_s2220(evento):
    """Gera PDF do ASO (S-2220) - Com assinatura do funcionário"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    from datetime import datetime

    buffer = BytesIO()

    # Configuração da página
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm
    )

    # Função para desenhar bordas pretas
    def bordas_pretas(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1.5)
        canvas.rect(
            1.2 * cm, 1.2 * cm,
            A4[0] - 2.4 * cm,
            A4[1] - 2.4 * cm,
        )
        canvas.restoreState()

    styles = getSampleStyleSheet()

    # Estilos profissionais
    estilo_titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Title'],
        fontSize=13,
        alignment=TA_CENTER,
        spaceAfter=4,
        spaceBefore=2,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )

    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=8,
        textColor=colors.black,
        fontName='Helvetica'
    )

    estilo_secao = ParagraphStyle(
        'Secao',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=5,
        spaceBefore=5,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )

    estilo_campo = ParagraphStyle(
        'Campo',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )

    estilo_valor = ParagraphStyle(
        'Valor',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica'
    )

    story = []

    func = evento.funcionario
    empresa = func.empresa

    # Função formatar data
    def formatar_data(valor):
        if not valor:
            return ""
        if hasattr(valor, 'strftime'):
            return valor.strftime('%d/%m/%Y')
        if isinstance(valor, str):
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y%m%d']:
                try:
                    data_obj = datetime.strptime(valor, fmt)
                    return data_obj.strftime('%d/%m/%Y')
                except:
                    continue
            return valor
        return str(valor)

    # ================= CABEÇALHO =================
    story.append(Paragraph("MINISTÉRIO DO TRABALHO E EMPREGO", estilo_titulo_principal))
    story.append(Paragraph("Programa de Controle Médico de Saúde Ocupacional", estilo_subtitulo))
    story.append(Paragraph("ATESTADO DE SAÚDE OCUPACIONAL - ASO", estilo_titulo_principal))
    story.append(Spacer(1, 0.3 * cm))

    # ================= 1. IDENTIFICAÇÃO DA EMPRESA =================
    story.append(Paragraph("1. IDENTIFICAÇÃO DA EMPRESA", estilo_secao))

    dados_empresa = [
        [Paragraph("<b>Razão Social:</b>", estilo_campo), Paragraph(empresa.nome or "", estilo_valor)],
        [Paragraph("<b>CNPJ:</b>", estilo_campo), Paragraph(empresa.cnpj or "", estilo_valor)],
        [Paragraph("<b>Endereço:</b>", estilo_campo),
         Paragraph(f"{empresa.rua or ''}, {empresa.bairro or ''} - {empresa.cidade or ''}/{empresa.estado or ''}",
                   estilo_valor)],
    ]

    tabela_empresa = Table(dados_empresa, colWidths=[3.2 * cm, 11.3 * cm])
    tabela_empresa.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tabela_empresa)
    story.append(Spacer(1, 0.2 * cm))

    # ================= 2. DADOS DO TRABALHADOR =================
    story.append(Paragraph("2. DADOS DO TRABALHADOR", estilo_secao))

    nascimento_str = formatar_data(func.nascimento)
    admissao_str = formatar_data(func.admissao)

    dados_trabalhador = [
        [Paragraph("<b>Nome:</b>", estilo_campo), Paragraph(func.nome or "", estilo_valor),
         Paragraph("<b>CPF:</b>", estilo_campo), Paragraph(func.cpf or "", estilo_valor)],
        [Paragraph("<b>Matrícula eSocial:</b>", estilo_campo),
         Paragraph(func.matricula_esocial or "NÃO INFORMADA", estilo_valor),
         Paragraph("<b>Nascimento:</b>", estilo_campo), Paragraph(nascimento_str, estilo_valor)],
        [Paragraph("<b>Admissão:</b>", estilo_campo), Paragraph(admissao_str, estilo_valor),
         Paragraph("<b>CBO:</b>", estilo_campo), Paragraph(func.cbo or "", estilo_valor)],
        [Paragraph("<b>Função:</b>", estilo_campo), Paragraph(func.funcao or "", estilo_valor),
         Paragraph("", estilo_campo), Paragraph("", estilo_valor)],
    ]

    tabela_trabalhador = Table(dados_trabalhador, colWidths=[3 * cm, 3.8 * cm, 2.5 * cm, 5.2 * cm])
    tabela_trabalhador.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tabela_trabalhador)
    story.append(Spacer(1, 0.2 * cm))

    # ================= 3. INFORMAÇÕES DO ASO =================
    story.append(Paragraph("3. INFORMAÇÕES DO ASO", estilo_secao))

    data_aso_str = formatar_data(evento.data_aso)

    dados_aso = [
        [Paragraph("<b>Data do ASO:</b>", estilo_campo), Paragraph(data_aso_str, estilo_valor),
         Paragraph("<b>CRM Médico:</b>", estilo_campo),
         Paragraph(f"{evento.crm_medico}/{evento.uf_crm}" if evento.crm_medico else "", estilo_valor)],
        [Paragraph("<b>CPF do Médico:</b>", estilo_campo),
         Paragraph(evento.cpf_medico or "Não informado", estilo_valor),
         Paragraph("", estilo_campo), Paragraph("", estilo_valor)],
    ]

    tabela_aso = Table(dados_aso, colWidths=[3 * cm, 3.8 * cm, 2.5 * cm, 5.2 * cm])
    tabela_aso.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tabela_aso)
    story.append(Spacer(1, 0.2 * cm))

    # ================= 4. EXAMES REALIZADOS =================
    if evento.exames and len(evento.exames) > 0:
        story.append(Paragraph("4. EXAMES REALIZADOS", estilo_secao))

        dados_exames = [["DATA", "TIPO DE EXAME", "RESULTADO"]]

        for exame in evento.exames[:4]:
            dados_exames.append([
                formatar_data(exame.data_exame),
                exame.tipo_exame or '',
                (exame.resultado[:35] + '...') if len(exame.resultado or '') > 35 else (exame.resultado or '')
            ])

        tabela_exames = Table(dados_exames, colWidths=[2.2 * cm, 5 * cm, 7.3 * cm])
        tabela_exames.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
            ('GRID', (0, 1), (-1, -1), 0.3, colors.lightgrey),
        ]))
        story.append(tabela_exames)
        story.append(Spacer(1, 0.2 * cm))

    # ================= 5. CONCLUSÃO =================
    story.append(Paragraph("5. CONCLUSÃO", estilo_secao))
    story.append(Paragraph(
        "O trabalhador acima identificado foi submetido aos exames constantes neste ASO, "
        "encontrando-se APTO para o exercício de suas funções, conforme NR-07.",
        estilo_valor
    ))
    story.append(Spacer(1, 0.4 * cm))

    # ================= ASSINATURAS (2 colunas) =================
    story.append(Paragraph("6. ASSINATURAS", estilo_secao))
    story.append(Spacer(1, 0.2 * cm))

    # Tabela com duas colunas de assinatura
    dados_assinaturas = [
        [
            Paragraph("<b>FUNCIONÁRIO</b>", estilo_campo),
            Paragraph("<b>MÉDICO RESPONSÁVEL</b>", estilo_campo)
        ],
        [
            Paragraph("_" * 35, estilo_valor),
            Paragraph("_" * 35, estilo_valor)
        ],
        [
            Paragraph(f"{func.nome or '_________________'}", estilo_valor),
            Paragraph(f"{evento.crm_medico}/{evento.uf_crm}" if evento.crm_medico else "CRM: _________________",
                      estilo_valor)
        ],
        [
            Paragraph("Assinatura do Funcionário", estilo_valor),
            Paragraph("Assinatura do Médico", estilo_valor)
        ],
        [
            Paragraph(f"Data: {formatar_data(datetime.now())}", estilo_valor),
            Paragraph(f"Data: {formatar_data(datetime.now())}", estilo_valor)
        ],
    ]

    tabela_assinaturas = Table(dados_assinaturas, colWidths=[7 * cm, 7 * cm])
    tabela_assinaturas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8')),
    ]))
    story.append(tabela_assinaturas)

    story.append(Spacer(1, 0.3 * cm))

    # ================= RODAPÉ =================
    story.append(Paragraph("<hr color='black' size='0.5'/>", styles['Normal']))
    rodape = Paragraph(
        "<font size=7>Documento eletrônico gerado conforme leiaute do eSocial (S-2220)</font>",
        estilo_valor
    )
    story.append(rodape)

    # Gerar PDF
    doc.build(story, onFirstPage=bordas_pretas, onLaterPages=bordas_pretas)
    buffer.seek(0)
    return buffer

# ================= ROTAS S-2221 =================


@app.route('/s2221/list')
@login_required
def list_s2221():
    eventos = EventoS2221.query.all()
    return render_template('eventos/s2221_list.html', eventos=eventos)


@app.route('/s2221/create', methods=['GET', 'POST'])
@login_required
def create_s2221():
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        e = EventoS2221(
            funcionario_id=request.form['funcionario_id'],
            data_exame=datetime.strptime(request.form['data_exame'], '%Y-%m-%d'),
            tipo_exame=request.form['tipo_exame'],
            resultado=request.form['resultado'],
            laboratorio=request.form.get('laboratorio')
        )
        db.session.add(e)
        db.session.commit()
        flash('Evento S-2221 criado!')
        return redirect(url_for('list_s2221'))
    return render_template('eventos/s2221_create.html', funcionarios=funcionarios)


@app.route('/s2221/delete/<int:id>')
@login_required
def delete_s2221(id):
    evento = EventoS2221.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento S-2221 excluído!')
    return redirect(url_for('list_s2221'))


@app.route('/s2221/send/<int:id>')
@login_required
def send_s2221(id):
    evento = EventoS2221.query.get_or_404(id)
    if evento.status != 'pendente':
        flash('Este evento já foi enviado!')
        return redirect(url_for('list_s2221'))
    cfg = ConfigCertificado.query.first()
    if not cfg:
        flash('Configure o certificado digital antes de enviar!')
        return redirect(url_for('config_certificado'))
    try:
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        xml = gerar_xml_s2221(evento, evento.funcionario.empresa, evento.funcionario, cfg.ambiente)
        xml_assinado = assinar_xml(xml, cert_pem, key_pem)
        recibo = enviar_lote(xml_assinado, cfg.ambiente)
        evento.xml_enviado = xml_assinado
        evento.recibo = recibo
        evento.status = 'enviado'
        db.session.commit()
        flash('Evento enviado com sucesso!')
    except Exception as e:
        flash(f'Erro ao enviar: {str(e)}')
    return redirect(url_for('list_s2221'))


@app.route('/s2221/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_s2221(id):
    evento = EventoS2221.query.get_or_404(id)
    funcionarios = Funcionario.query.all()

    if request.method == 'POST':
        evento.funcionario_id = request.form['funcionario_id']
        evento.data_exame = datetime.strptime(request.form['data_exame'], '%Y-%m-%d').date()
        evento.tipo_exame = request.form['tipo_exame']
        evento.resultado = request.form['resultado']
        evento.laboratorio = request.form.get('laboratorio')
        evento.cpf_responsavel = request.form['cpf_responsavel']

        # Validar CPF
        if not validar_cpf(evento.cpf_responsavel):
            flash('CPF do responsável inválido!', 'danger')
            return redirect(url_for('edit_s2221', id=id))

        db.session.commit()
        flash('Evento S-2221 atualizado!', 'success')
        return redirect(url_for('list_s2221'))

    return render_template('eventos/s2221_edit.html', evento=evento, funcionarios=funcionarios)


@app.route('/processar_s2221', methods=['POST'])
@login_required
def processar_s2221():
    try:
        funcionario_id = request.form.get('funcionario_id')
        data_exame = request.form.get('data_exame')
        tipo_exame = request.form.get('tipo_exame')
        resultado = request.form.get('resultado')
        laboratorio = request.form.get('laboratorio')
        cpf_responsavel = request.form.get('cpf_responsavel')
        apenas_xml = request.form.get('apenas_xml') == 'true'

        # ================= VALIDAÇÕES =================

        # Validar campos obrigatórios
        if not funcionario_id:
            return "Campo 'funcionário' é obrigatório", 400
        if not data_exame:
            return "Campo 'data do exame' é obrigatório", 400
        if not tipo_exame:
            return "Campo 'tipo de exame' é obrigatório", 400
        if not resultado:
            return "Campo 'resultado' é obrigatório", 400
        if not cpf_responsavel:
            return "Campo 'CPF do responsável' é obrigatório", 400

        # Validar CPF do responsável
        if not validar_cpf(cpf_responsavel):
            return f"CPF do responsável inválido: {cpf_responsavel}", 400

        # Validar se funcionário existe
        funcionario = db.session.get(Funcionario, int(funcionario_id))
        if not funcionario:
            return f"Funcionário ID {funcionario_id} não encontrado", 404

        # Validar se funcionário tem matrícula e CBO
        if not funcionario.matricula_esocial or not funcionario.cbo:
            return "Funcionário sem matrícula eSocial ou CBO cadastrado", 400

        # ================= PROCESSAMENTO =================

        # Se for apenas gerar XML
        if apenas_xml:
            try:
                # Criar evento temporário
                evento_temp = EventoS2221(
                    funcionario_id=funcionario.id,
                    data_exame=datetime.strptime(data_exame, '%Y-%m-%d').date(),
                    tipo_exame=tipo_exame,
                    resultado=resultado,
                    laboratorio=laboratorio,
                    cpf_responsavel=cpf_responsavel
                )

                # Gerar XML
                xml_gerado = gerar_xml_s2221(evento_temp, funcionario.empresa, funcionario, '2')
                buffer = BytesIO(xml_gerado.encode('utf-8'))

                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=f'S2221_{funcionario.nome.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml',
                    mimetype='application/xml'
                )
            except Exception as e:
                print(f"Erro ao gerar XML: {str(e)}")
                return f"Erro ao gerar XML: {str(e)}", 500

        # ================= SALVAR NO BANCO DE DADOS =================

        try:
            # Criar evento
            evento = EventoS2221(
                funcionario_id=funcionario.id,
                data_exame=datetime.strptime(data_exame, '%Y-%m-%d').date(),
                tipo_exame=tipo_exame,
                resultado=resultado,
                laboratorio=laboratorio,
                cpf_responsavel=cpf_responsavel
            )
            db.session.add(evento)
            db.session.commit()

            flash('Evento S-2221 criado com sucesso!', 'success')
            return redirect(url_for('list_s2221'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar no banco: {str(e)}")
            return f"Erro ao salvar evento: {str(e)}", 500

    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return f"Erro interno do servidor: {str(e)}", 500
@app.route('/s2221/view_xml/<int:id>')
@login_required
def view_xml_s2221(id):
    """Visualizar XML do evento S-2221"""
    try:
        evento = EventoS2221.query.get_or_404(id)
        funcionario = evento.funcionario
        empresa = funcionario.empresa
        xml_str = gerar_xml_s2221(evento, empresa, funcionario, '2')
        return Response(xml_str, mimetype='application/xml')
    except Exception as e:
        flash(f'Erro ao gerar XML: {str(e)}', 'danger')
        return redirect(url_for('list_s2221'))

########################################################### EVENTO S 2220 #############################
def gerar_xml_s2220(evento, empresa, funcionario, ambiente='2'):
    """
    Gera XML do evento S-2220 (ASO)
    CPF do médico é opcional
    """
    from datetime import datetime

    # Tratamento para CPF do médico (opcional)
    cpf_medico = ""
    if evento.cpf_medico:
        # Remove caracteres não numéricos se houver
        cpf_medico = ''.join(filter(str.isdigit, evento.cpf_medico))

    # Tratamento para CNPJ da empresa
    cnpj_empresa = ''.join(filter(str.isdigit, empresa.cnpj)) if empresa.cnpj else ""

    # Tratamento para CPF do funcionário
    cpf_funcionario = ''.join(filter(str.isdigit, funcionario.cpf)) if funcionario.cpf else ""

    # Tratamento para matrícula eSocial
    matricula = funcionario.matricula_esocial or ""

    # Data do ASO
    if hasattr(evento.data_aso, 'strftime'):
        data_aso = evento.data_aso.strftime('%Y-%m-%d')
    else:
        data_aso = str(evento.data_aso)

    # Monta o XML
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtASO/v_S_01_02_00">
    <evtASO Id="ID{evento.id}">
        <ideEvento>
            <indRetif>1</indRetif>
            <nrRecibo/>
            <tpAmb>{ambiente}</tpAmb>
            <procEmi>1</procEmi>
            <verProc>1.0</verProc>
        </ideEvento>
        <ideEmpregador>
            <tpInsc>1</tpInsc>
            <nrInsc>{cnpj_empresa}</nrInsc>
        </ideEmpregador>
        <trabalhador>
            <cpfTrab>{cpf_funcionario}</cpfTrab>
            <matricula>{matricula}</matricula>
        </trabalhador>
        <aso>
            <dtAso>{data_aso}</dtAso>
            <medico>
                <crmMed>{evento.crm_medico}</crmMed>
                <ufCrm>{evento.uf_crm}</ufCrm>'''

    # Só adiciona o CPF se ele existir
    if cpf_medico:
        xml += f'''
                <cpfMed>{cpf_medico}</cpfMed>'''

    xml += '''
            </medico>
            <exames>'''

    # Adiciona os exames
    for exame in evento.exames:
        if hasattr(exame.data_exame, 'strftime'):
            data_exame = exame.data_exame.strftime('%Y-%m-%d')
        else:
            data_exame = str(exame.data_exame)

        xml += f'''
                <exame>
                    <dtExame>{data_exame}</dtExame>
                    <tpExame>{exame.tipo_exame}</tpExame>
                    <resultadoExame>{exame.resultado}</resultadoExame>
                </exame>'''

    xml += '''
            </exames>
        </aso>
    </evtASO>
</eSocial>'''

    return xml

@app.route('/processar_s2220', methods=['POST'])
@login_required
def processar_s2220():
    try:
        funcionario_id = request.form.get('funcionario_id')
        data_aso = request.form.get('data_aso')
        crm_medico = request.form.get('crm_medico')
        uf_crm = request.form.get('uf_crm')
        cpf_medico = request.form.get('cpf_medico')  # Agora é opcional
        apenas_xml = request.form.get('apenas_xml') == 'true'

        # ================= VALIDAÇÕES =================

        # Validar campos obrigatórios
        if not funcionario_id:
            return "Campo 'funcionário' é obrigatório", 400
        if not data_aso:
            return "Campo 'data do ASO' é obrigatório", 400
        if not crm_medico:
            return "Campo 'CRM do médico' é obrigatório", 400
        if not uf_crm:
            return "Campo 'UF do CRM' é obrigatório", 400

        # Validar CPF do médico apenas se foi preenchido
        if cpf_medico and not validar_cpf(cpf_medico):
            return f"CPF do médico inválido: {cpf_medico}", 400

        # Validar se funcionário existe
        funcionario = db.session.get(Funcionario, int(funcionario_id))
        if not funcionario:
            return f"Funcionário ID {funcionario_id} não encontrado", 404

        # Validar se funcionário tem matrícula e CBO
        if not funcionario.matricula_esocial or not funcionario.cbo:
            return "Funcionário sem matrícula eSocial ou CBO cadastrado", 400

        # Capturar exames
        datas_exame = request.form.getlist('data_exame[]')
        tipos_exame = request.form.getlist('tipo_exame[]')
        resultados = request.form.getlist('resultado[]')

        exames = []
        for i in range(len(datas_exame)):
            if datas_exame[i] and tipos_exame[i] and resultados[i]:
                exames.append({
                    'data_exame': datetime.strptime(datas_exame[i], '%Y-%m-%d').date(),
                    'tipo_exame': tipos_exame[i],
                    'resultado': resultados[i]
                })

        # ================= PROCESSAMENTO =================

        # Se for apenas gerar XML (não salvar no banco)
        if apenas_xml:
            try:
                # Criar evento temporário
                evento_temp = EventoS2220(
                    funcionario_id=funcionario.id,
                    data_aso=datetime.strptime(data_aso, '%Y-%m-%d').date(),
                    crm_medico=crm_medico,
                    uf_crm=uf_crm,
                    cpf_medico=cpf_medico if cpf_medico else ''  # Se vazio, salva como string vazia
                )

                # Adicionar exames temporários
                for ex in exames:
                    exame_temp = S2220Exame(
                        data_exame=ex['data_exame'],
                        tipo_exame=ex['tipo_exame'],
                        resultado=ex['resultado']
                    )
                    evento_temp.exames.append(exame_temp)

                # Gerar XML
                xml_gerado = gerar_xml_s2220(evento_temp, funcionario.empresa, funcionario, '2')
                buffer = BytesIO(xml_gerado.encode('utf-8'))

                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=f'S2220_{funcionario.nome.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml',
                    mimetype='application/xml'
                )
            except Exception as e:
                print(f"Erro ao gerar XML: {str(e)}")
                return f"Erro ao gerar XML: {str(e)}", 500

        # ================= SALVAR NO BANCO DE DADOS =================

        try:
            # Criar evento
            evento = EventoS2220(
                funcionario_id=funcionario.id,
                data_aso=datetime.strptime(data_aso, '%Y-%m-%d').date(),
                crm_medico=crm_medico,
                uf_crm=uf_crm,
                cpf_medico=cpf_medico if cpf_medico else ''  # Se vazio, salva como string vazia
            )
            db.session.add(evento)
            db.session.flush()  # Para obter o ID do evento

            # Adicionar exames
            for ex in exames:
                exame_obj = S2220Exame(
                    evento_id=evento.id,
                    data_exame=ex['data_exame'],
                    tipo_exame=ex['tipo_exame'],
                    resultado=ex['resultado']
                )
                db.session.add(exame_obj)

            db.session.commit()

            flash('Evento S-2220 criado com sucesso!', 'success')
            return redirect(url_for('list_s2220'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar no banco: {str(e)}")
            return f"Erro ao salvar evento: {str(e)}", 500

    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return f"Erro interno do servidor: {str(e)}", 500





@app.route('/s2220/view_pdf/<int:id>')
@login_required
def view_pdf_s2220(id):
    """Visualizar PDF do ASO no navegador"""
    try:
        evento = EventoS2220.query.get_or_404(id)
        pdf_buffer = gerar_pdf_s2220(evento)

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False  # False para exibir no navegador
        )
    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('list_s2220'))



######################################################## ================= ROTAS S-2210 =================

@app.route('/s2210/create', methods=['GET'])
@login_required  # ← Adicione este decorator também
def create_s2210():
    funcionarios = Funcionario.query.all()
    return render_template('eventos/s2210_create.html', funcionarios=funcionarios)


@app.route('/s2210/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_s2210(id):
    evento = EventoS2210.query.get_or_404(id)
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        evento.funcionario_id = request.form['funcionario_id']
        evento.data_acidente = datetime.strptime(request.form['data_acidente'], '%Y-%m-%d').date()
        evento.hora_acidente = datetime.strptime(request.form['hora_acidente'], '%H:%M').time()
        evento.tipo_cat = request.form['tipo_cat']
        evento.tipo_acidente = request.form['tipo_acidente']
        evento.local = request.form['local']
        evento.parte_atingida = request.form['parte_atingida']
        evento.descricao = request.form['descricao']
        evento.cpf_responsavel = request.form['cpf_responsavel']
        db.session.commit()
        flash('Evento S-2210 atualizado!', 'success')  # ← Adicione 'success'
        return redirect(url_for('list_s2210'))
    return render_template('eventos/s2210_edit.html', evento=evento, funcionarios=funcionarios)

@app.route('/s2210/delete/<int:id>')
@login_required
def delete_s2210(id):
    evento = EventoS2210.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento S-2210 excluído!')
    return redirect(url_for('list_s2210'))


@app.route('/s2210/send/<int:id>')
@login_required
def send_s2210(id):
    evento = EventoS2210.query.get_or_404(id)
    if evento.status != 'pendente':
        flash('Este evento já foi enviado!')
        return redirect(url_for('list_s2210'))
    cfg = ConfigCertificado.query.first()
    if not cfg:
        flash('Configure o certificado digital antes de enviar!')
        return redirect(url_for('config_certificado'))
    try:
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        empresa = evento.funcionario.empresa
        xml = gerar_xml_s2210(evento, empresa, evento.funcionario, cfg.ambiente)
        xml_assinado = assinar_xml(xml, cert_pem, key_pem)
        recibo = enviar_lote(xml_assinado, cfg.ambiente)
        evento.xml_enviado = xml_assinado
        evento.recibo = recibo
        evento.status = 'enviado'
        db.session.commit()
        flash('Evento enviado com sucesso!')
    except Exception as e:
        flash(f'Erro ao enviar: {str(e)}')
    return redirect(url_for('list_s2210'))


@app.route('/s2210/list')
@login_required
def list_s2210():
    eventos = EventoS2210.query.all()
    return render_template('eventos/s2210_list.html', eventos=eventos)


@app.route('/processar_s2210', methods=['POST'])
@login_required
def processar_s2210():
    try:
        funcionario_id = request.form.get('funcionario_id')
        data_acidente = request.form.get('data_acidente')
        hora_acidente = request.form.get('hora_acidente')
        tipo_cat = request.form.get('tipo_cat')
        tipo_acidente = request.form.get('tipo_acidente')
        local = request.form.get('local')
        parte_atingida = request.form.get('parte_atingida')
        descricao = request.form.get('descricao')
        cpf_responsavel = request.form.get('cpf_responsavel')
        apenas_xml = request.form.get('apenas_xml') == 'true'

        # ================= VALIDAÇÕES =================

        # Validar campos obrigatórios
        if not funcionario_id:
            return "Campo 'funcionário' é obrigatório", 400
        if not data_acidente:
            return "Campo 'data do acidente' é obrigatório", 400
        if not hora_acidente:
            return "Campo 'hora do acidente' é obrigatório", 400
        if not tipo_cat:
            return "Campo 'tipo de CAT' é obrigatório", 400
        if not tipo_acidente:
            return "Campo 'tipo de acidente' é obrigatório", 400
        if not local:
            return "Campo 'local do acidente' é obrigatório", 400
        if not parte_atingida:
            return "Campo 'parte atingida' é obrigatório", 400
        if not descricao:
            return "Campo 'descrição' é obrigatório", 400
        if not cpf_responsavel:
            return "Campo 'CPF do responsável' é obrigatório", 400

        # Validar CPF do responsável
        if not validar_cpf(cpf_responsavel):
            return f"CPF do responsável inválido: {cpf_responsavel}", 400

        # Validar se funcionário existe
        funcionario = db.session.get(Funcionario, int(funcionario_id))
        if not funcionario:
            return f"Funcionário ID {funcionario_id} não encontrado", 404

        # Validar se funcionário tem matrícula e CBO
        if not funcionario.matricula_esocial or not funcionario.cbo:
            return "Funcionário sem matrícula eSocial ou CBO cadastrado", 400

        # ================= PROCESSAMENTO =================

        # Se for apenas gerar XML (não salvar no banco)
        if apenas_xml:
            try:
                # Criar evento temporário
                evento_temp = EventoS2210(
                    funcionario_id=funcionario.id,
                    data_acidente=datetime.strptime(data_acidente, '%Y-%m-%d').date(),
                    hora_acidente=datetime.strptime(hora_acidente, '%H:%M').time(),
                    tipo_cat=tipo_cat,
                    tipo_acidente=tipo_acidente,
                    local=local,
                    parte_atingida=parte_atingida,
                    descricao=descricao,
                    cpf_responsavel=cpf_responsavel
                )

                # Gerar XML
                xml_gerado = gerar_xml_s2210(evento_temp, funcionario.empresa, funcionario, '2')
                buffer = BytesIO(xml_gerado.encode('utf-8'))

                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=f'S2210_{funcionario.nome.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml',
                    mimetype='application/xml'
                )
            except Exception as e:
                print(f"Erro ao gerar XML: {str(e)}")
                return f"Erro ao gerar XML: {str(e)}", 500

        # ================= SALVAR NO BANCO DE DADOS =================

        try:
            # Criar evento
            evento = EventoS2210(
                funcionario_id=funcionario.id,
                data_acidente=datetime.strptime(data_acidente, '%Y-%m-%d').date(),
                hora_acidente=datetime.strptime(hora_acidente, '%H:%M').time(),
                tipo_cat=tipo_cat,
                tipo_acidente=tipo_acidente,
                local=local,
                parte_atingida=parte_atingida,
                descricao=descricao,
                cpf_responsavel=cpf_responsavel
            )
            db.session.add(evento)
            db.session.commit()

            flash('Evento S-2210 criado com sucesso!', 'success')
            return redirect(url_for('list_s2210'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar no banco: {str(e)}")
            return f"Erro ao salvar evento: {str(e)}", 500

    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return f"Erro interno do servidor: {str(e)}", 500


# ================= ROTAS S-2240 =================
TABELA_24_AGENTES = RISCOS_OCUPACIONAIS = [
    # Código especial para NENHUM RISCO
    {"codigo": "00.00.000", "descricao": "Nenhum risco identificado"},

    # Físicos
    {"codigo": "01.01.001", "descricao": "Ruído contínuo ou intermitente"},
    {"codigo": "01.01.002", "descricao": "Ruído de impacto"},
    {"codigo": "01.02.001", "descricao": "Vibração localizada"},
    {"codigo": "01.02.002", "descricao": "Vibração de corpo inteiro"},
    {"codigo": "01.03.001", "descricao": "Calor (sobrecarga térmica)"},
    {"codigo": "01.03.002", "descricao": "Frio"},
    {"codigo": "01.04.001", "descricao": "Radiação ionizante"},
    {"codigo": "01.04.002", "descricao": "Radiação não ionizante (luz, laser, UV, infravermelho, micro-ondas, radiofrequência)"},
    {"codigo": "01.05.001", "descricao": "Pressões anormais (hiperbárica, hipobárica)"},
    {"codigo": "01.06.001", "descricao": "Umidade"},

    # Químicos
    {"codigo": "02.01.001", "descricao": "Sílica livre cristalizada"},
    {"codigo": "02.01.002", "descricao": "Asbesto (amianto)"},
    {"codigo": "02.02.001", "descricao": "Benzeno"},
    {"codigo": "02.02.002", "descricao": "Chumbo metálico"},
    {"codigo": "02.02.003", "descricao": "Mercúrio"},
    {"codigo": "02.02.004", "descricao": "Cádmio"},
    {"codigo": "02.02.005", "descricao": "Cromo hexavalente"},
    {"codigo": "02.03.001", "descricao": "Hidrocarbonetos aromáticos (tolueno, xileno, etc.)"},
    {"codigo": "02.03.002", "descricao": "Solventes clorados (tricloroetileno, percloroetileno)"},
    {"codigo": "02.04.001", "descricao": "Poeiras minerais (carvão, caulim, talco, etc.)"},
    {"codigo": "02.04.002", "descricao": "Poeiras vegetais (algodão, madeira, grãos, etc.)"},
    {"codigo": "02.05.001", "descricao": "Fumos metálicos (soldagem, corte)"},
    {"codigo": "02.06.001", "descricao": "Gases e vapores (CO2, SO2, NH3, Cl2, etc.)"},

    # Biológicos
    {"codigo": "03.01.001", "descricao": "Bactérias (Bacillus anthracis, Leptospira, etc.)"},
    {"codigo": "03.02.001", "descricao": "Vírus (Hepatite B, HIV, Hantavírus, etc.)"},
    {"codigo": "03.03.001", "descricao": "Parasitas (malária, toxoplasmose, etc.)"},
    {"codigo": "03.04.001", "descricao": "Fungos (microtoxinas, histoplasmose, etc.)"},

    # Ergonômicos
    {"codigo": "04.01.001", "descricao": "Levantamento e transporte manual de peso"},
    {"codigo": "04.02.001", "descricao": "Movimentos repetitivos"},
    {"codigo": "04.03.001", "descricao": "Posturas inadequadas"},
    {"codigo": "04.04.001", "descricao": "Jornada de trabalho prolongada / excessiva"},
    {"codigo": "04.05.001", "descricao": "Trabalho noturno"},
    {"codigo": "04.06.001", "descricao": "Monitoramento de tela (computador) sem pausas"},

    # Mecânicos / Acidentes
    {"codigo": "05.01.001", "descricao": "Máquinas e equipamentos sem proteção"},
    {"codigo": "05.02.001", "descricao": "Risco de quedas em altura"},
    {"codigo": "05.02.002", "descricao": "Risco de quedas no mesmo nível"},
    {"codigo": "05.03.001", "descricao": "Eletricidade (contato direto/indireto)"},
    {"codigo": "05.04.001", "descricao": "Incêndio / explosão"},
    {"codigo": "05.05.001", "descricao": "Arranjo físico inadequado (espaço reduzido, obstáculos)"},
    {"codigo": "05.06.001", "descricao": "Iluminação insuficiente ou excessiva"},

    # Organizacionais / Psicossociais
    {"codigo": "06.01.001", "descricao": "Trabalho sob pressão (assédio moral, metas abusivas)"},
    {"codigo": "06.02.001", "descricao": "Conflitos interpessoais"},
    {"codigo": "06.03.001", "descricao": "Isolamento profissional / trabalho solitário"},
    {"codigo": "06.04.001", "descricao": "Falta de autonomia / controle sobre tarefas"},
    {"codigo": "06.05.001", "descricao": "Dupla jornada de trabalho (externo + doméstico)"}
]


@app.route('/s2240/list')
@login_required
def list_s2240():
    eventos = EventoS2240.query.all()
    return render_template('eventos/s2240_list.html', eventos=eventos)


@app.route('/s2240/create')
@login_required
def create_s2240():
    funcionarios = Funcionario.query.all()
    return render_template('eventos/s2240_create.html',
                           funcionarios=funcionarios,
                           tabela24=TABELA_24_AGENTES)


@app.route('/s2240/delete/<int:id>')
@login_required
def delete_s2240(id):
    evento = EventoS2240.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento S-2240 excluído!')
    return redirect(url_for('list_s2240'))


@app.route('/s2240/send/<int:id>')
@login_required
def send_s2240(id):
    evento = EventoS2240.query.get_or_404(id)
    if evento.status != 'pendente':
        flash('Este evento já foi enviado!')
        return redirect(url_for('list_s2240'))
    cfg = ConfigCertificado.query.first()
    if not cfg:
        flash('Configure o certificado digital antes de enviar!')
        return redirect(url_for('config_certificado'))
    try:
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        xml = gerar_xml_s2240(evento, evento.funcionario.empresa, evento.funcionario, cfg.ambiente)
        xml_assinado = assinar_xml(xml, cert_pem, key_pem)
        recibo = enviar_lote(xml_assinado, cfg.ambiente)
        evento.xml_enviado = xml_assinado
        evento.recibo = recibo
        evento.status = 'enviado'
        db.session.commit()
        flash('Evento enviado com sucesso!')
    except Exception as e:
        flash(f'Erro ao enviar: {str(e)}')
    return redirect(url_for('list_s2240'))


@app.route('/processar_s2240', methods=['POST'])
@login_required
def processar_s2240():
    from datetime import datetime  # ← IMPORTANTE!
    import traceback
    from io import BytesIO
    from flask import send_file

    try:
        # Captura os dados do formulário
        funcionario_id = request.form.get('funcionario_id')
        data_avaliacao_str = request.form.get('data_avaliacao')
        cpf_avaliador = request.form.get('cpf_avaliador')
        apenas_xml = request.form.get('apenas_xml') == 'true'

        # Captura os riscos
        riscos = []
        codigos = request.form.getlist('agente_codigo[]')
        intensidades = request.form.getlist('intensidade[]')
        epis = request.form.getlist('epi_utilizado[]')

        for i in range(len(codigos)):
            if codigos[i]:
                riscos.append({
                    'codigo_agente': codigos[i],
                    'intensidade': intensidades[i] if i < len(intensidades) else '',
                    'epi': epis[i] if i < len(epis) else ''
                })

        # Busca o funcionário
        funcionario = db.session.get(Funcionario, funcionario_id)
        if not funcionario:
            flash('Funcionário não encontrado', 'danger')
            return redirect(url_for('create_s2240'))

        print("Dados recebidos:", dict(request.form))
        print("Riscos:", riscos)

        # Converte a data
        data_avaliacao = datetime.strptime(data_avaliacao_str, '%Y-%m-%d').date()

        # Se for apenas gerar XML
        if apenas_xml:
            try:
                # Cria evento temporário
                evento_temp = EventoS2240(
                    funcionario_id=funcionario.id,
                    data_avaliacao=data_avaliacao,
                    cpf_avaliador=cpf_avaliador
                )

                # Adiciona riscos
                for r in riscos:
                    risco_temp = RiscoS2240(
                        codigo_agente=r['codigo_agente'],
                        intensidade=r['intensidade'],
                        epi_utilizado=r['epi']
                    )
                    evento_temp.riscos.append(risco_temp)

                # Gera XML
                xml_gerado = gerar_xml_s2240(evento_temp, funcionario.empresa, funcionario, '2')

                if not xml_gerado:
                    raise Exception("Função gerar_xml_s2240 retornou vazio ou None")

                buffer = BytesIO(xml_gerado.encode('utf-8'))

                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=f'S2240_{funcionario.nome.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xml',
                    mimetype='application/xml'
                )
            except Exception as e:
                print(f"Erro ao gerar XML: {str(e)}")
                traceback.print_exc()
                flash(f'Erro ao gerar XML: {str(e)}', 'danger')
                return redirect(url_for('create_s2240'))

        # Salvar no banco
        try:
            evento = EventoS2240(
                funcionario_id=funcionario.id,
                data_avaliacao=data_avaliacao,
                cpf_avaliador=cpf_avaliador
            )
            db.session.add(evento)
            db.session.flush()

            for r in riscos:
                risco = RiscoS2240(
                    evento_id=evento.id,
                    codigo_agente=r['codigo_agente'],
                    intensidade=r['intensidade'],
                    epi_utilizado=r['epi']
                )
                db.session.add(risco)

            db.session.commit()
            flash('Evento S-2240 criado com sucesso!', 'success')
            return redirect(url_for('list_s2240'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar: {str(e)}")
            traceback.print_exc()
            flash(f'Erro ao salvar: {str(e)}', 'danger')
            return redirect(url_for('create_s2240'))

    except Exception as e:
        print(f"Erro geral: {str(e)}")
        traceback.print_exc()
        flash(f'Erro no processamento: {str(e)}', 'danger')
        return redirect(url_for('create_s2240'))

@app.route('/enviar_xml_manual', methods=['GET', 'POST'])
@login_required
def enviar_xml_manual():
    from esocial_utils import carregar_certificado, assinar_xml, enviar_lote
    if request.method == 'POST':
        xml_file = request.files.get('xml_file')
        if not xml_file:
            flash('Nenhum arquivo selecionado', 'danger')
            return redirect(url_for('enviar_xml_manual'))
        xml_content = xml_file.read().decode('utf-8')
        cfg = ConfigCertificado.query.first()
        if not cfg:
            flash('Configure o certificado digital primeiro!', 'danger')
            return redirect(url_for('config_certificado'))
        try:
            cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
            xml_assinado = assinar_xml(xml_content, cert_pem, key_pem)
            resposta = enviar_lote(xml_assinado, cfg.ambiente)
            flash('XML enviado com sucesso! Recibo recebido.', 'success')
        except Exception as e:
            flash(f'Erro ao enviar: {str(e)}', 'danger')
        return redirect(url_for('enviar_xml_manual'))
    return render_template('enviar_xml_manual.html')
@app.route('/s2240/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_s2240(id):
    evento = EventoS2240.query.get_or_404(id)
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        evento.funcionario_id = request.form['funcionario_id']
        evento.data_avaliacao = datetime.strptime(request.form['data_avaliacao'], '%Y-%m-%d').date()
        evento.cpf_avaliador = request.form['cpf_avaliador']
        db.session.commit()
        flash('Evento S-2240 atualizado!', 'success')
        return redirect(url_for('list_s2240'))
    return render_template('eventos/s2240_edit.html', evento=evento, funcionarios=funcionarios)


def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro
    Aceita formatos: 123.456.789-09, 12345678909, 123.456.78909
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', str(cpf))

    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False

    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False

    # Cálculo do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[9]):
        return False

    # Cálculo do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0

    return resto == int(cpf[10])

################################################################# certificado #############################
def carregar_certificado(pfx_path, senha):
    """Carrega certificado A1 no formato .pfx com melhor tratamento de erro"""
    try:
        with open(pfx_path, 'rb') as f:
            pfx_data = f.read()

        # Tentar diferentes encodings para a senha
        try:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data,
                senha.encode('utf-8')
            )
        except Exception:
            try:
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    pfx_data,
                    senha.encode('latin-1')
                )
            except Exception:
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    pfx_data,
                    senha.encode('cp1252')
                )

        if certificate is None:
            raise Exception("Certificado não encontrado no arquivo")

        # Converte para PEM
        cert_pem = certificate.public_bytes(Encoding.PEM).decode('utf-8')
        key_pem = private_key.private_bytes(
            Encoding.PEM,
            PrivateFormat.PKCS8,
            NoEncryption()
        ).decode('utf-8')

        print("✅ Certificado carregado com sucesso!")
        return cert_pem, key_pem

    except Exception as e:
        print(f"❌ Erro ao carregar certificado: {e}")
        raise Exception(
            f"Erro ao carregar certificado: Verifique a senha e o arquivo. Detalhe: {str(e)}"
        )


@app.route('/s2220/enviar/<int:id>')
@login_required
def enviar_s2220(id):
    evento = db.session.get(EventoS2220, id)
    if not evento:
        flash('Evento não encontrado!', 'error')
        return redirect(url_for('list_s2220'))

    if evento.status == 'enviado':
        flash('Este evento já foi enviado!', 'warning')
        return redirect(url_for('list_s2220'))

    # Verificar modo de envio
    modo_envio = session.get('modo_envio', False)

    # Buscar configuração do certificado
    cfg = ConfigCertificado.query.first()

    if not cfg and modo_envio:
        flash('Configure o certificado digital antes de enviar em modo PRODUÇÃO!', 'danger')
        return redirect(url_for('config_certificado'))

    try:
        funcionario = evento.funcionario
        empresa = funcionario.empresa

        # Validar dados obrigatórios
        if not empresa.cnpj:
            flash('Empresa sem CNPJ configurado!', 'error')
            return redirect(url_for('list_s2220'))

        if not funcionario.matricula_esocial:
            flash('Funcionário sem matrícula eSocial!', 'error')
            return redirect(url_for('list_s2220'))

        if not funcionario.cpf:
            flash('Funcionário sem CPF!', 'error')
            return redirect(url_for('list_s2220'))

        # Modo TESTE - Simular envio
        if not modo_envio:
            # Simular envio
            import uuid
            recibo_simulado = f"SIMULADO_{uuid.uuid4().hex[:16]}"

            evento.status = 'enviado'
            evento.recibo = recibo_simulado
            evento.data_envio = datetime.utcnow()

            # Gerar XML mesmo em modo teste
            try:
                xml_gerado = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')
                evento.xml_enviado = xml_gerado
            except Exception as xml_err:
                print(f"Erro ao gerar XML: {str(xml_err)}")
                evento.xml_enviado = f"<!-- Erro ao gerar XML: {str(xml_err)} -->"

            db.session.commit()

            flash(f'✅ Evento enviado em MODO TESTE! Recibo: {recibo_simulado}', 'success')
            return redirect(url_for('list_s2220'))

        # Modo PRODUÇÃO - Envio real
        ambiente = cfg.ambiente if cfg.ambiente else '1'

        # Carregar certificado
        if not cfg.certificado_pfx or not os.path.exists(cfg.certificado_pfx):
            flash('Arquivo de certificado não encontrado!', 'error')
            return redirect(url_for('config_certificado'))

        # Verificar se a senha existe
        if not cfg.senha:
            flash('Senha do certificado não configurada!', 'error')
            return redirect(url_for('config_certificado'))

        try:
            cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)

            if not cert_pem or not key_pem:
                flash('Erro ao carregar certificado!', 'error')
                return redirect(url_for('config_certificado'))
        except Exception as cert_err:
            flash(f'Erro ao carregar certificado: {str(cert_err)}', 'error')
            return redirect(url_for('config_certificado'))

        # Gerar XML
        try:
            xml = gerar_xml_s2220(evento, empresa, funcionario, ambiente)

            if not xml or len(xml.strip()) == 0:
                flash('Erro ao gerar XML: XML vazio!', 'error')
                return redirect(url_for('list_s2220'))
        except Exception as xml_err:
            flash(f'Erro ao gerar XML: {str(xml_err)}', 'error')
            return redirect(url_for('list_s2220'))

        # Assinar XML
        try:
            xml_assinado = assinar_xml(xml, cert_pem, key_pem)

            if not xml_assinado or len(xml_assinado.strip()) == 0:
                flash('Erro ao assinar XML: XML assinado vazio!', 'error')
                return redirect(url_for('list_s2220'))
        except Exception as sign_err:
            flash(f'Erro ao assinar XML: {str(sign_err)}', 'error')
            return redirect(url_for('list_s2220'))

        # Enviar lote
        try:
            recibo = enviar_lote(xml_assinado, ambiente)

            if not recibo:
                flash('Erro ao enviar: Recibo vazio!', 'error')
                return redirect(url_for('list_s2220'))
        except Exception as send_err:
            flash(f'Erro ao enviar para o eSocial: {str(send_err)}', 'error')
            return redirect(url_for('list_s2220'))

        # Atualizar evento
        evento.xml_enviado = xml_assinado
        evento.recibo = recibo
        evento.status = 'enviado'
        evento.data_envio = datetime.utcnow()
        db.session.commit()

        flash('Evento enviado com sucesso para o eSocial!', 'success')

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        flash(f'Erro ao enviar: {str(e)}', 'danger')

    return redirect(url_for('list_s2220'))


@app.route('/ver_recibo/<int:id>')
@login_required
def ver_recibo(id):
    evento = db.session.get(EventoS2220, id)
    if not evento or not evento.recibo:
        flash('Recibo não encontrado!', 'error')
        return redirect(url_for('list_s2220'))

    # Retorna o recibo como texto puro
    return Response(
        evento.recibo,
        mimetype='text/plain',
        headers={'Content-Disposition': f'inline; filename=recibo_{id}.txt'}
    )
# ================= ENVIO S-2221 (MODO TESTE) =================
@app.route('/s2221/enviar/<int:id>')
@login_required
def enviar_s2221(id):
    import traceback
    from functions_s2221 import gerar_xml_s2221
    from esocial_utils import enviar_lote, carregar_certificado, assinar_xml
    from models import ReciboEnvio
    from datetime import datetime

    try:
        evento = db.session.get(EventoS2221, id)
        if not evento:
            flash('Evento não encontrado', 'danger')
            return redirect(url_for('list_s2221'))

        print(f"\n{'=' * 50}")
        print(f"ENVIANDO S-2221 ID: {id}")
        print(f"{'=' * 50}")

        cfg = ConfigCertificado.query.first()
        if not cfg:
            flash('Configure o certificado digital primeiro!', 'danger')
            return redirect(url_for('config_certificado'))

        # Gera XML
        xml_gerado = gerar_xml_s2221(
            evento,
            evento.funcionario.empresa,
            evento.funcionario
        )

        if not xml_gerado:
            flash('Erro: XML gerado está vazio', 'danger')
            return redirect(url_for('list_s2221'))

        print(f"✅ XML gerado: {len(xml_gerado)} bytes")

        # Carrega certificado e assina
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        xml_assinado = assinar_xml(xml_gerado, cert_pem, key_pem)

        # Envia
        resposta = enviar_lote(xml_assinado, str(cfg.ambiente))

        print(f"Resposta: {resposta}")

        # CORREÇÃO: Salva recibo (resposta é string)
        nome_xml = f"S2221_{evento.funcionario.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

        recibo = ReciboEnvio(
            evento_tipo="S-2221",
            evento_id=evento.id,
            nome_xml=nome_xml,
            recibo=str(resposta),  # resposta é string
            data_envio=datetime.now(),
            status="enviado",
            mensagem_erro=""
        )
        db.session.add(recibo)

        evento.status = "enviado"
        evento.data_envio = datetime.now()
        db.session.commit()

        flash('Evento S-2221 enviado com sucesso!', 'success')

    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        traceback.print_exc()
        flash(f'Erro ao enviar: {str(e)}', 'danger')

    return redirect(url_for('list_s2221'))

# ================= ENVIO S-2210 (MODO TESTE) =================
@app.route('/s2210/enviar/<int:id>')
@login_required
def enviar_s2210(id):
    import traceback
    from functions_s2210 import gerar_xml_s2210
    from esocial_utils import enviar_lote, carregar_certificado, assinar_xml
    from models import ReciboEnvio
    from datetime import datetime

    try:
        evento = db.session.get(EventoS2210, id)
        if not evento:
            flash('Evento não encontrado', 'danger')
            return redirect(url_for('list_s2210'))

        print(f"\n{'=' * 50}")
        print(f"ENVIANDO S-2210 ID: {id}")
        print(f"{'=' * 50}")

        cfg = ConfigCertificado.query.first()
        if not cfg:
            flash('Configure o certificado digital primeiro!', 'danger')
            return redirect(url_for('config_certificado'))

        # Gera XML
        xml_gerado = gerar_xml_s2210(
            evento,
            evento.funcionario.empresa,
            evento.funcionario
        )

        if not xml_gerado:
            flash('Erro: XML gerado está vazio', 'danger')
            return redirect(url_for('list_s2210'))

        print(f"✅ XML gerado: {len(xml_gerado)} bytes")

        # Carrega certificado e assina
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        xml_assinado = assinar_xml(xml_gerado, cert_pem, key_pem)

        # Envia
        resposta = enviar_lote(xml_assinado, str(cfg.ambiente))

        print(f"Resposta: {resposta}")

        # CORREÇÃO: Salva recibo (resposta é string, não dicionário)
        nome_xml = f"S2210_{evento.funcionario.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

        recibo = ReciboEnvio(
            evento_tipo="S-2210",
            evento_id=evento.id,
            nome_xml=nome_xml,
            recibo=str(resposta),  # resposta é string
            data_envio=datetime.now(),
            status="enviado",
            mensagem_erro=""
        )
        db.session.add(recibo)

        evento.status = "enviado"
        evento.data_envio = datetime.now()
        db.session.commit()

        flash('Evento S-2210 enviado com sucesso!', 'success')

    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        traceback.print_exc()
        flash(f'Erro ao enviar: {str(e)}', 'danger')

    return redirect(url_for('list_s2210'))

# ================= ENVIO S-2240 (MODO TESTE) =================
@app.route('/s2240/enviar/<int:id>')
@login_required
def enviar_s2240(id):
    import traceback
    from functions_s2240 import gerar_xml_s2240
    from esocial_utils import enviar_lote, carregar_certificado, assinar_xml
    from models import ReciboEnvio

    try:
        evento = db.session.get(EventoS2240, id)
        if not evento:
            flash('Evento não encontrado', 'danger')
            return redirect(url_for('list_s2240'))

        print(f"\n{'=' * 50}")
        print(f"ENVIANDO S-2240 ID: {id}")
        print(f"{'=' * 50}")

        # Verifica certificado
        cfg = ConfigCertificado.query.first()
        if not cfg:
            flash('Configure o certificado digital primeiro!', 'danger')
            return redirect(url_for('config_certificado'))

        # Gera XML
        xml_gerado = gerar_xml_s2240(
            evento,
            evento.funcionario.empresa,
            evento.funcionario
        )

        if not xml_gerado:
            flash('Erro: XML gerado está vazio', 'danger')
            return redirect(url_for('list_s2240'))

        # Carrega e assina
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        xml_assinado = assinar_xml(xml_gerado, cert_pem, key_pem)

        # Envia
        resposta = enviar_lote(xml_assinado, str(cfg.ambiente))

        # SALVA O RECIBO
        nome_xml = f"S2240_{evento.funcionario.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"

        recibo = ReciboEnvio(
            evento_tipo='S-2240',
            evento_id=evento.id,
            protocolo=resposta.get('protocolo', ''),
            status='enviado',
            resposta_completa=str(resposta),
            data_envio=datetime.now(),
            funcionario_id=evento.funcionario_id,
            nome_xml=nome_xml
        )
        db.session.add(recibo)

        # Atualiza status do evento
        evento.status = 'enviado'
        evento.data_envio = datetime.now()

        db.session.commit()

        flash('Evento S-2240 enviado com sucesso!', 'success')

    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        traceback.print_exc()
        flash(f'Erro ao enviar: {str(e)}', 'danger')

    return redirect(url_for('list_s2240'))


@app.route('/recibos')
@login_required
def listar_recibos():
    from models import ReciboEnvio, EventoS2220, EventoS2210, EventoS2221, EventoS2240
    from sqlalchemy import or_

    # Base query
    query = ReciboEnvio.query

    # Filtros
    tipo = request.args.get('tipo')
    status = request.args.get('status')
    funcionario_nome = request.args.get('funcionario')

    if tipo:
        query = query.filter_by(evento_tipo=tipo)
    if status:
        query = query.filter_by(status=status)

    # Busca todos os recibos
    recibos = query.order_by(ReciboEnvio.data_envio.desc()).all()

    # Filtro por nome do funcionário (pós-processamento)
    if funcionario_nome:
        recibos_filtrados = []
        for recibo in recibos:
            try:
                if recibo.evento_tipo == 'S-2220':
                    evento = db.session.get(EventoS2220, recibo.evento_id)
                    nome = evento.funcionario.nome if evento and evento.funcionario else ''
                elif recibo.evento_tipo == 'S-2210':
                    evento = db.session.get(EventoS2210, recibo.evento_id)
                    nome = evento.funcionario.nome if evento and evento.funcionario else ''
                elif recibo.evento_tipo == 'S-2221':
                    evento = db.session.get(EventoS2221, recibo.evento_id)
                    nome = evento.funcionario.nome if evento and evento.funcionario else ''
                elif recibo.evento_tipo == 'S-2240':
                    evento = db.session.get(EventoS2240, recibo.evento_id)
                    nome = evento.funcionario.nome if evento and evento.funcionario else ''
                else:
                    nome = ''

                if funcionario_nome.lower() in nome.lower():
                    recibos_filtrados.append(recibo)
            except:
                pass
        recibos = recibos_filtrados

    # Adiciona nome do funcionário ao objeto recibo
    for recibo in recibos:
        try:
            if recibo.evento_tipo == 'S-2220':
                evento = db.session.get(EventoS2220, recibo.evento_id)
                recibo.funcionario_nome = evento.funcionario.nome if evento and evento.funcionario else 'N/A'
            elif recibo.evento_tipo == 'S-2210':
                evento = db.session.get(EventoS2210, recibo.evento_id)
                recibo.funcionario_nome = evento.funcionario.nome if evento and evento.funcionario else 'N/A'
            elif recibo.evento_tipo == 'S-2221':
                evento = db.session.get(EventoS2221, recibo.evento_id)
                recibo.funcionario_nome = evento.funcionario.nome if evento and evento.funcionario else 'N/A'
            elif recibo.evento_tipo == 'S-2240':
                evento = db.session.get(EventoS2240, recibo.evento_id)
                recibo.funcionario_nome = evento.funcionario.nome if evento and evento.funcionario else 'N/A'
            else:
                recibo.funcionario_nome = 'N/A'
        except:
            recibo.funcionario_nome = 'N/A'

    return render_template('recibos_list.html', recibos=recibos)


@app.route('/recibos/detalhe/<int:id>')
@login_required
def recibo_detalhe(id):
    from models import ReciboEnvio, EventoS2220, EventoS2210, EventoS2221, EventoS2240

    recibo = db.session.get(ReciboEnvio, id)
    if not recibo:
        flash('Recibo não encontrado', 'danger')
        return redirect(url_for('listar_recibos'))

    # Busca o evento relacionado
    evento = None
    if recibo.evento_tipo == 'S-2220':
        evento = db.session.get(EventoS2220, recibo.evento_id)
    elif recibo.evento_tipo == 'S-2210':
        evento = db.session.get(EventoS2210, recibo.evento_id)
    elif recibo.evento_tipo == 'S-2221':
        evento = db.session.get(EventoS2221, recibo.evento_id)
    elif recibo.evento_tipo == 'S-2240':
        evento = db.session.get(EventoS2240, recibo.evento_id)

    return render_template('recibos_detalhe.html', recibo=recibo, evento=evento)


@app.route('/recibos/pdf/<int:id>')
@login_required
def recibo_pdf(id):
    from models import ReciboEnvio, EventoS2220, EventoS2210, EventoS2221, EventoS2240
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit
    from io import BytesIO
    from flask import make_response
    from datetime import datetime

    recibo = db.session.get(ReciboEnvio, id)
    if not recibo:
        flash('Recibo não encontrado', 'danger')
        return redirect(url_for('listar_recibos'))

    # Busca o evento relacionado
    evento = None
    if recibo.evento_tipo == 'S-2220':
        evento = db.session.get(EventoS2220, recibo.evento_id)
    elif recibo.evento_tipo == 'S-2210':
        evento = db.session.get(EventoS2210, recibo.evento_id)
    elif recibo.evento_tipo == 'S-2221':
        evento = db.session.get(EventoS2221, recibo.evento_id)
    elif recibo.evento_tipo == 'S-2240':
        evento = db.session.get(EventoS2240, recibo.evento_id)

    # Cria o PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"COMPROVANTE DE ENVIO - {recibo.evento_tipo}")

    # Linha
    p.line(50, height - 60, width - 50, height - 60)

    # Dados do recibo
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 90, "DADOS DO RECIBO:")

    p.setFont("Helvetica", 10)
    p.drawString(50, height - 110, f"ID do Recibo: {recibo.id}")
    p.drawString(50, height - 125, f"Tipo de Evento: {recibo.evento_tipo}")
    p.drawString(50, height - 140,
                 f"Data de Envio: {recibo.data_envio.strftime('%d/%m/%Y %H:%M:%S') if recibo.data_envio else 'N/A'}")
    p.drawString(50, height - 155, f"Status: {recibo.status}")

    # Funcionário
    if evento and hasattr(evento, 'funcionario') and evento.funcionario:
        p.drawString(50, height - 175, f"Funcionário: {evento.funcionario.nome}")
        p.drawString(50, height - 190, f"CPF: {evento.funcionario.cpf}")

    # Recibo/Protocolo
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 220, "PROTOCOLO/RECIBO:")
    p.setFont("Helvetica", 10)

    # Quebra o texto do recibo em múltiplas linhas
    recibo_texto = recibo.recibo if recibo.recibo else "N/A"
    linhas = simpleSplit(recibo_texto, "Helvetica", 10, width - 100)
    y = height - 240
    for linha in linhas:
        p.drawString(50, y, linha)
        y -= 15

    # Nome do XML
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y - 20, "ARQUIVO XML:")
    p.setFont("Helvetica", 10)
    p.drawString(50, y - 40, recibo.nome_xml if recibo.nome_xml else "N/A")

    # Mensagem de erro se houver
    if recibo.mensagem_erro:
        p.setFillColorRGB(1, 0, 0)
        p.drawString(50, y - 65, f"ERRO: {recibo.mensagem_erro}")
        p.setFillColorRGB(0, 0, 0)

    # Rodapé
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 50, f"Documento gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    p.drawString(50, 35, "Sistema SST - Gerenciamento de Riscos Ocupacionais")

    p.showPage()
    p.save()

    buffer.seek(0)
    return make_response(buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'inline; filename=recibo_{recibo.id}_{recibo.evento_tipo}.pdf'
    })
@app.route('/debug/respostas')
@login_required
def debug_respostas():
    """Lista as respostas do eSocial salvas para debug"""
    import glob
    arquivos = glob.glob('resposta_esocial_*.xml')
    arquivos.sort(reverse=True)

    return render_template('debug_respostas.html', arquivos=arquivos)


@app.route('/debug/resposta/<nome>')
@login_required
def debug_ver_resposta(nome):
    """Visualiza uma resposta específica"""
    import os
    if os.path.exists(nome):
        with open(nome, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        return Response(conteudo, mimetype='text/xml')
    return "Arquivo não encontrado", 404


def gerar_pdf_recibo(recibo_info):
    """Gera PDF do recibo para entregar ao cliente - Versão simplificada"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f"Recibo_eSocial_{recibo_info['evento_tipo']}_{recibo_info['id']}"
    )

    styles = getSampleStyleSheet()

    # Cores
    cor_primaria = colors.HexColor('#2c3e50')
    cor_secundaria = colors.HexColor('#3498db')
    cor_sucesso = colors.HexColor('#27ae60')
    cor_borda = colors.HexColor('#bdc3c7')

    # Estilos personalizados
    style_titulo = ParagraphStyle(
        name='Titulo',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=cor_primaria,
        alignment=1,
        spaceAfter=30,
        fontName='Helvetica-Bold'
    )

    style_subtitulo = ParagraphStyle(
        name='Subtitulo',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=cor_secundaria,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )

    style_normal = ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        spaceAfter=6
    )

    style_codigo = ParagraphStyle(
        name='Codigo',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Courier',
        textColor=colors.HexColor('#333333'),
        backColor=colors.HexColor('#f5f5f5'),
        leftIndent=10,
        rightIndent=10,
        spaceAfter=10
    )

    # Função para cabeçalho e rodapé
    def add_header_footer(canvas, doc):
        canvas.saveState()

        # Cabeçalho
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(cor_primaria)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 10, "COMPROVANTE DE ENVIO - eSocial")

        # Linha do cabeçalho
        canvas.setStrokeColor(cor_borda)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - 15,
                    doc.width + doc.leftMargin, doc.height + doc.topMargin - 15)

        # Rodapé
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 10,
                          f"Documento gerado eletronicamente em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 10, f"Página {doc.page}")

        canvas.restoreState()

    story = []

    # Título
    story.append(Paragraph("COMPROVANTE DE ENVIO AO eSOCIAL", style_titulo))
    story.append(Spacer(1, 20))

    # Informações do evento
    story.append(Paragraph("DADOS DO EVENTO", style_subtitulo))

    dados_evento = [
        ["Tipo de Evento:", recibo_info['evento_tipo']],
        ["ID do Evento:", str(recibo_info['id'])],
        ["Funcionário:", recibo_info['funcionario_nome']],
        ["CPF:", recibo_info['funcionario_cpf']],
        ["Data do Evento:", recibo_info['data_evento']],
        ["Data de Envio:", recibo_info['data_envio']],
    ]

    tabela_evento = Table(dados_evento, colWidths=[5 * cm, 11 * cm])
    tabela_evento.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(tabela_evento)
    story.append(Spacer(1, 20))

    # Recibo - Versão simplificada sem HTML
    story.append(Paragraph("RECIBO DO eSOCIAL", style_subtitulo))

    # Limpa o recibo - remove tags HTML se houver
    recibo_limpo = recibo_info['recibo']
    # Se for HTML, pega apenas o texto relevante
    if recibo_limpo.startswith('<!DOCTYPE') or recibo_limpo.startswith('<html'):
        recibo_limpo = "Recibo recebido do eSocial. Consulte o sistema para mais detalhes."

    # Adiciona o recibo como texto plano
    story.append(Paragraph(recibo_limpo.replace('\n', '<br/>'), style_codigo))
    story.append(Spacer(1, 20))

    # Status
    story.append(Paragraph("STATUS DO ENVIO", style_subtitulo))

    status_cor = cor_sucesso if recibo_info['status'] == 'enviado' else colors.HexColor('#e74c3c')
    status_texto = "ENVIADO COM SUCESSO" if recibo_info['status'] == 'enviado' else "ERRO NO ENVIO"

    story.append(Paragraph(f"<font color='{status_cor}'><b>{status_texto}</b></font>", style_normal))
    story.append(Spacer(1, 20))

    # Informações do XML
    story.append(Paragraph("INFORMAÇÕES DO ARQUIVO", style_subtitulo))

    dados_xml = [
        ["Nome do Arquivo:", recibo_info['nome_xml']],
        ["Tamanho:", recibo_info['tamanho_xml']],
    ]

    tabela_xml = Table(dados_xml, colWidths=[5 * cm, 11 * cm])
    tabela_xml.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, cor_borda),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(tabela_xml)
    story.append(Spacer(1, 30))

    # Assinatura
    story.append(Paragraph("_________________________________________", style_normal))
    story.append(Paragraph("Assinatura do Responsável", style_normal))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<font size='8'>Sistema SST - {datetime.now().strftime('%Y')}</font>", style_normal))

    # Rodapé adicional
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<font size='8' color='grey'>Este documento comprova o envio do evento ao sistema eSocial. Em caso de dúvidas, consulte o sistema.</font>",
        style_normal))

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer

@app.route('/recibo/pdf/<tipo>/<int:id>')
@login_required
def download_recibo_pdf(tipo, id):
    """Baixar PDF do recibo"""
    try:
        from io import BytesIO
        from datetime import datetime

        recibo_info = None

        if tipo == 's2220':
            evento = EventoS2220.query.get_or_404(id)
            if evento.recibo:
                recibo_info = {
                    'id': evento.id,
                    'evento_tipo': 'S-2220 - ASO (Atestado de Saúde Ocupacional)',
                    'funcionario_nome': evento.funcionario.nome,
                    'funcionario_cpf': evento.funcionario.cpf,
                    'data_evento': evento.data_aso.strftime('%d/%m/%Y'),
                    'data_envio': evento.data_envio.strftime(
                        '%d/%m/%Y %H:%M:%S') if evento.data_envio else 'Não informada',
                    'recibo': evento.recibo,
                    'status': evento.status,
                    'nome_xml': f'S2220_{evento.funcionario.nome}_{evento.data_aso}.xml',
                    'tamanho_xml': f"{len(evento.xml_enviado or '') / 1024:.2f} KB" if evento.xml_enviado else 'N/A'
                }

        elif tipo == 's2221':
            evento = EventoS2221.query.get_or_404(id)
            if evento.recibo:
                recibo_info = {
                    'id': evento.id,
                    'evento_tipo': 'S-2221 - Exame Toxicológico',
                    'funcionario_nome': evento.funcionario.nome,
                    'funcionario_cpf': evento.funcionario.cpf,
                    'data_evento': evento.data_exame.strftime('%d/%m/%Y'),
                    'data_envio': evento.data_envio.strftime(
                        '%d/%m/%Y %H:%M:%S') if evento.data_envio else 'Não informada',
                    'recibo': evento.recibo,
                    'status': evento.status,
                    'nome_xml': f'S2221_{evento.funcionario.nome}_{evento.data_exame}.xml',
                    'tamanho_xml': f"{len(evento.xml_enviado or '') / 1024:.2f} KB" if evento.xml_enviado else 'N/A'
                }

        elif tipo == 's2210':
            evento = EventoS2210.query.get_or_404(id)
            if evento.recibo:
                recibo_info = {
                    'id': evento.id,
                    'evento_tipo': 'S-2210 - CAT (Comunicação de Acidente de Trabalho)',
                    'funcionario_nome': evento.funcionario.nome,
                    'funcionario_cpf': evento.funcionario.cpf,
                    'data_evento': evento.data_acidente.strftime('%d/%m/%Y'),
                    'data_envio': evento.data_envio.strftime(
                        '%d/%m/%Y %H:%M:%S') if evento.data_envio else 'Não informada',
                    'recibo': evento.recibo,
                    'status': evento.status,
                    'nome_xml': f'S2210_{evento.funcionario.nome}_{evento.data_acidente}.xml',
                    'tamanho_xml': f"{len(evento.xml_enviado or '') / 1024:.2f} KB" if evento.xml_enviado else 'N/A'
                }

        elif tipo == 's2240':
            evento = EventoS2240.query.get_or_404(id)
            if evento.recibo:
                recibo_info = {
                    'id': evento.id,
                    'evento_tipo': 'S-2240 - Condições Ambientais do Trabalho',
                    'funcionario_nome': evento.funcionario.nome,
                    'funcionario_cpf': evento.funcionario.cpf,
                    'data_evento': evento.data_avaliacao.strftime('%d/%m/%Y'),
                    'data_envio': evento.data_envio.strftime(
                        '%d/%m/%Y %H:%M:%S') if evento.data_envio else 'Não informada',
                    'recibo': evento.recibo,
                    'status': evento.status,
                    'nome_xml': f'S2240_{evento.funcionario.nome}_{evento.data_avaliacao}.xml',
                    'tamanho_xml': f"{len(evento.xml_enviado or '') / 1024:.2f} KB" if evento.xml_enviado else 'N/A'
                }

        if not recibo_info:
            flash('Recibo não encontrado para este evento', 'warning')
            return redirect(url_for('listar_recibos'))

        pdf_buffer = gerar_pdf_recibo(recibo_info)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f"Recibo_{tipo.upper()}_{id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        flash(f'Erro ao gerar PDF do recibo: {str(e)}', 'danger')
        print(f"Erro detalhado: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('listar_recibos'))

@app.context_processor
def utility_processor():
    """Disponibiliza variáveis para todos os templates"""
    # Não importe MODO_REAL do esocial_utils
    # Use a função get_modo_envio()
    return dict(modo_envio=get_modo_envio())


# ================= CONFIGURAÇÃO DO MODO =================
def get_modo_envio():
    """Retorna o modo atual de envio (True=Produção, False=Teste)"""
    from models import ConfigSistema
    try:
        config = ConfigSistema.query.filter_by(chave='modo_envio').first()
        if not config:
            config = ConfigSistema(chave='modo_envio', valor='false')
            db.session.add(config)
            db.session.commit()
            return False
        return config.valor.lower() == 'true'
    except Exception as e:
        print(f"Erro ao ler modo envio: {e}")
        return False


def set_modo_envio(modo_producao):
    """Define o modo de envio"""
    from models import ConfigSistema
    try:
        config = ConfigSistema.query.filter_by(chave='modo_envio').first()
        if not config:
            config = ConfigSistema(chave='modo_envio', valor='false')
            db.session.add(config)

        config.valor = 'true' if modo_producao else 'false'
        config.atualizado_em = datetime.now()
        db.session.commit()
        print(f"Modo alterado para: {'PRODUÇÃO' if modo_producao else 'TESTE'}")
    except Exception as e:
        print(f"Erro ao salvar modo envio: {e}")
        db.session.rollback()



# Adicione estas funções no main.py (antes do utility_processor)



@app.route('/toggle_modo_envio', methods=['POST'])
@login_required
def toggle_modo_envio():
    """Alterna entre modo teste e produção"""
    if current_user.tipo != 'admin':
        flash('Apenas administradores podem alterar o modo de envio', 'danger')
        return redirect(url_for('dashboard'))

    modo_atual = get_modo_envio()
    set_modo_envio(not modo_atual)

    novo_modo = "PRODUÇÃO" if not modo_atual else "TESTE"
    flash(f'✅ Modo de envio alterado para: {novo_modo}', 'success')

    return redirect(request.referrer or url_for('dashboard'))
@app.context_processor
def utility_processor():
    """Disponibiliza variáveis para todos os templates"""
    return dict(modo_envio=get_modo_envio())


@app.route('/minha-empresa/certificado', methods=['GET', 'POST'])
@login_required
def minha_empresa_certificado():
    # Verifica se o usuário tem uma empresa
    empresa = Empresa.query.filter_by(usuario_id=current_user.id).first()

    if not empresa:
        flash('Cadastre uma empresa primeiro.', 'warning')
        return redirect(url_for('empresa_create'))

    if request.method == 'POST':
        # Processar upload do certificado
        certificado_file = request.files.get('certificado')
        senha_certificado = request.form.get('senha_certificado')

        if certificado_file and senha_certificado:
            # Salvar certificado
            filename = secure_filename(f"cert_{empresa.id}.p12")
            certificado_path = os.path.join('certificados', filename)
            certificado_file.save(certificado_path)

            # Salvar no banco
            empresa.certificado_path = certificado_path
            empresa.senha_certificado = senha_certificado
            db.session.commit()

            flash('Certificado digital enviado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Selecione o arquivo do certificado e informe a senha.', 'danger')

    return render_template('minha_empresa_certificado.html', empresa=empresa)
@app.route('/minha-empresa/certificado/remover')
@login_required
def remover_certificado_empresa():
    empresa = Empresa.query.filter_by(usuario_id=current_user.id).first()
    if empresa:
        config = ConfigCertificado.query.filter_by(empresa_id=empresa.id).first()
        if config:
            # Remove o arquivo
            if os.path.exists(config.certificado_pfx):
                os.remove(config.certificado_pfx)
            db.session.delete(config)
            db.session.commit()
            flash('✅ Certificado removido com sucesso!', 'success')
    return redirect(url_for('meu_certificado_empresa'))

#########################################################  MODELOS DE DOCUMENTOS PARA OS CLIENTES #########


# Configuração para upload de modelos
UPLOAD_FOLDER_MODELOS = 'modelos_documentos'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

if not os.path.exists(UPLOAD_FOLDER_MODELOS):
    os.makedirs(UPLOAD_FOLDER_MODELOS)


def allowed_modelo_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Rotas para administrador gerenciar modelos
@app.route('/admin/modelos')
@login_required
@admin_required
def admin_modelos():
    """Lista todos os modelos de documentos"""
    modelos = ModeloDocumento.query.order_by(ModeloDocumento.data_criacao.desc()).all()
    return render_template('admin/modelos_list.html', modelos=modelos)


@app.route('/admin/modelos/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_modelo_novo():
    """Criar novo modelo de documento"""
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        versao = request.form.get('versao', '1.0')
        campos_variaveis = request.form.get('campos_variaveis', '')

        # Upload do arquivo PDF
        arquivo_pdf = request.files.get('arquivo_pdf')
        arquivo_path = None

        if arquivo_pdf and allowed_modelo_file(arquivo_pdf.filename):
            filename = secure_filename(f"modelo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arquivo_pdf.filename}")
            arquivo_path = os.path.join(UPLOAD_FOLDER_MODELOS, filename)
            arquivo_pdf.save(arquivo_path)

        # Upload do arquivo Word
        arquivo_word = request.files.get('arquivo_word')
        arquivo_word_path = None

        if arquivo_word and allowed_modelo_file(arquivo_word.filename):
            filename = secure_filename(
                f"modelo_word_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arquivo_word.filename}")
            arquivo_word_path = os.path.join(UPLOAD_FOLDER_MODELOS, filename)
            arquivo_word.save(arquivo_word_path)

        modelo = ModeloDocumento(
            nome=nome,
            descricao=descricao,
            tipo=tipo,
            categoria=categoria,
            arquivo_path=arquivo_path,
            arquivo_word_path=arquivo_word_path,
            versao=versao,
            campos_variaveis=campos_variaveis,
            criado_por=current_user.id
        )

        db.session.add(modelo)
        db.session.commit()

        flash('Modelo de documento criado com sucesso!', 'success')
        return redirect(url_for('admin_modelos'))

    return render_template('admin/modelo_form.html', modelo=None)


@app.route('/admin/modelos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_modelo_editar(id):
    """Editar modelo de documento"""
    modelo = ModeloDocumento.query.get_or_404(id)

    if request.method == 'POST':
        modelo.nome = request.form.get('nome')
        modelo.descricao = request.form.get('descricao')
        modelo.tipo = request.form.get('tipo')
        modelo.categoria = request.form.get('categoria')
        modelo.versao = request.form.get('versao')
        modelo.campos_variaveis = request.form.get('campos_variaveis')
        modelo.ativo = request.form.get('ativo') == 'on'
        modelo.data_atualizacao = datetime.utcnow()

        # Upload novo PDF se enviado
        arquivo_pdf = request.files.get('arquivo_pdf')
        if arquivo_pdf and allowed_modelo_file(arquivo_pdf.filename):
            if modelo.arquivo_path and os.path.exists(modelo.arquivo_path):
                os.remove(modelo.arquivo_path)
            filename = secure_filename(f"modelo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arquivo_pdf.filename}")
            modelo.arquivo_path = os.path.join(UPLOAD_FOLDER_MODELOS, filename)
            arquivo_pdf.save(modelo.arquivo_path)

        # Upload novo Word se enviado
        arquivo_word = request.files.get('arquivo_word')
        if arquivo_word and allowed_modelo_file(arquivo_word.filename):
            if modelo.arquivo_word_path and os.path.exists(modelo.arquivo_word_path):
                os.remove(modelo.arquivo_word_path)
            filename = secure_filename(
                f"modelo_word_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arquivo_word.filename}")
            modelo.arquivo_word_path = os.path.join(UPLOAD_FOLDER_MODELOS, filename)
            arquivo_word.save(modelo.arquivo_word_path)

        db.session.commit()
        flash('Modelo atualizado com sucesso!', 'success')
        return redirect(url_for('admin_modelos'))

    return render_template('admin/modelo_form.html', modelo=modelo)


@app.route('/admin/modelos/excluir/<int:id>')
@login_required
@admin_required
def admin_modelo_excluir(id):
    """Excluir modelo de documento"""
    modelo = ModeloDocumento.query.get_or_404(id)

    # Remove arquivos físicos
    if modelo.arquivo_path and os.path.exists(modelo.arquivo_path):
        os.remove(modelo.arquivo_path)
    if modelo.arquivo_word_path and os.path.exists(modelo.arquivo_word_path):
        os.remove(modelo.arquivo_word_path)

    db.session.delete(modelo)
    db.session.commit()

    flash('Modelo excluído com sucesso!', 'success')
    return redirect(url_for('admin_modelos'))


# Rotas para clientes baixarem documentos
@app.route('/clientes/documentos')
@login_required
def clientes_documentos():
    """Página com documentos disponíveis para download"""
    modelos = ModeloDocumento.query.filter_by(ativo=True).order_by(ModeloDocumento.categoria,
                                                                   ModeloDocumento.nome).all()

    # Agrupar por categoria
    categorias = {}
    for modelo in modelos:
        cat = modelo.categoria or 'outros'
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(modelo)

    return render_template('cliente/documentos_disponiveis.html', categorias=categorias)


@app.route('/clientes/documentos/download/<int:modelo_id>')
@login_required
def cliente_download_documento(modelo_id):
    """Download do documento pelo cliente"""
    modelo = ModeloDocumento.query.get_or_404(modelo_id)

    if not modelo.ativo:
        flash('Documento não disponível', 'danger')
        return redirect(url_for('clientes_documentos'))

    tipo = request.args.get('tipo', 'pdf')

    if tipo == 'word' and modelo.arquivo_word_path:
        arquivo_path = modelo.arquivo_word_path
        nome_download = f"{modelo.nome.replace(' ', '_')}.docx"
    else:
        arquivo_path = modelo.arquivo_path
        nome_download = f"{modelo.nome.replace(' ', '_')}.pdf"

    if not arquivo_path or not os.path.exists(arquivo_path):
        flash('Arquivo não encontrado', 'danger')
        return redirect(url_for('clientes_documentos'))

    # Registrar download (opcional)
    # LogDownload.create(usuario=current_user.id, documento=modelo.id)

    return send_file(
        arquivo_path,
        as_attachment=True,
        download_name=nome_download,
        mimetype='application/pdf' if tipo == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


@app.route('/clientes/documentos/gerar/<int:modelo_id>', methods=['POST'])
@login_required
def cliente_gerar_documento(modelo_id):
    """Gerar documento personalizado com dados do cliente/funcionário"""
    modelo = ModeloDocumento.query.get_or_404(modelo_id)

    # Coletar dados do formulário para substituição
    dados = request.form.to_dict()

    # Buscar dados da empresa e funcionário
    empresa = Empresa.query.filter_by(usuario_id=current_user.id).first()
    funcionario_id = dados.get('funcionario_id')
    funcionario = Funcionario.query.get(funcionario_id) if funcionario_id else None

    # Substituir placeholders no documento
    substituicoes = {
        '[NOME_EMPRESA]': empresa.nome if empresa else '',
        '[CNPJ]': empresa.cnpj if empresa else '',
        '[NOME_FUNCIONARIO]': funcionario.nome if funcionario else '',
        '[CPF]': funcionario.cpf if funcionario else '',
        '[DATA_ATUAL]': datetime.now().strftime('%d/%m/%Y'),
        '[HORA_ATUAL]': datetime.now().strftime('%H:%M:%S'),
    }

    # Adicionar dados personalizados
    substituicoes.update(dados)

    # Gerar PDF personalizado
    if modelo.tipo in ['pdf', 'ambos']:
        pdf_path = gerar_pdf_personalizado(modelo, substituicoes)
        return send_file(pdf_path, as_attachment=True,
                         download_name=f"documento_{datetime.now().strftime('%Y%m%d')}.pdf")

    return redirect(url_for('clientes_documentos'))


def gerar_pdf_personalizado(modelo, substituicoes):
    """Função para gerar PDF com substituições"""
    # Esta é uma implementação básica - você pode expandir
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    output_path = os.path.join(UPLOAD_FOLDER_MODELOS, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Adicionar texto com substituições
    y = height - 50
    for key, value in substituicoes.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 20

    c.save()
    return output_path

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash('Acesso negado. Área restrita para administradores.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

####################################################  CONFIGURAÇÃO DO CERTIFICADO ESOCIAL ##########################
@app.route('/config_certificado', methods=['GET', 'POST'])
@login_required
def config_certificado():
    # Buscar a empresa do usuário atual
    # CORREÇÃO: Usar session.get em vez de query.get
    empresa = db.session.get(Empresa, current_user.empresa_id) if hasattr(current_user, 'empresa_id') else None

    # Se não encontrar empresa pelo usuário, tenta buscar a primeira empresa
    if not empresa:
        empresa = Empresa.query.first()

    # Se ainda não tem empresa, redireciona para criar
    if not empresa:
        flash('Cadastre uma empresa antes de configurar o certificado!', 'warning')
        return redirect(url_for('create_empresa'))

    if request.method == 'POST':
        try:
            certificado = request.files.get('certificado')
            senha = request.form.get('senha')
            ambiente = request.form.get('ambiente', '2')

            if not certificado or not certificado.filename:
                flash('Selecione um arquivo de certificado!', 'error')
                return redirect(url_for('config_certificado'))

            # Criar diretório se não existir
            cert_dir = os.path.join('uploads', 'certificados')
            os.makedirs(cert_dir, exist_ok=True)

            # Nome do arquivo usando CNPJ da empresa
            cnpj_limpo = ''.join(filter(str.isdigit, empresa.cnpj)) if empresa.cnpj else 'sem_cnpj'
            filename = secure_filename(f"{cnpj_limpo}_{certificado.filename}")
            filepath = os.path.join(cert_dir, filename)

            # Salvar arquivo
            certificado.save(filepath)

            # Verificar se já existe configuração
            config = ConfigCertificado.query.filter_by(empresa_id=empresa.id).first()

            if config:
                # Atualizar existente
                config.certificado_pfx = filepath
                config.senha = senha
                config.ambiente = ambiente
                config.data_config = datetime.utcnow()
            else:
                # Criar nova
                config = ConfigCertificado(
                    empresa_id=empresa.id,
                    usuario_id=current_user.id,
                    certificado_pfx=filepath,
                    senha=senha,
                    ambiente=ambiente
                )
                db.session.add(config)

            db.session.commit()
            flash('Certificado configurado com sucesso!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao configurar certificado: {str(e)}', 'error')
            return redirect(url_for('config_certificado'))

    # Buscar configuração existente
    config = ConfigCertificado.query.filter_by(empresa_id=empresa.id).first()

    return render_template('config_certificado.html',
                           empresa=empresa,
                           config=config,
                           modo_envio=session.get('modo_envio', False))


# ================= ROTAS DE psicossocial =================
# ==================== AVALIAÇÃO PSICOSSOCIAL ====================

@app.route('/clientes')
@login_required
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.data_cadastro.desc()).all()
    return render_template('clientes_list.html', clientes=clientes)


@app.route('/clientes/novo', methods=['GET', 'POST'])
@login_required
def novo_cliente():
    if request.method == 'POST':
        email = request.form['email']

        # Verifica se email já existe
        cliente_existente = Cliente.query.filter_by(email=email).first()
        if cliente_existente:
            flash('Este email já está cadastrado!', 'danger')
            return redirect(url_for('novo_cliente'))

        cliente = Cliente(
            nome=request.form['nome'],
            email=email,
            empresa=request.form.get('empresa', ''),
            telefone=request.form.get('telefone', '')
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_clientes'))

    return render_template('cliente_form.html')




import secrets
from urllib.parse import quote
from flask import request, url_for, render_template

@app.route('/nova_avaliacao_psicossocial/<int:cliente_id>', methods=['GET', 'POST'])
@login_required
def nova_avaliacao_psicossocial(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == 'POST':
        nome = request.form['nome_funcionario']
        email = request.form.get('email_funcionario')
        telefone = request.form['telefone']
        cargo = request.form['cargo']
        setor = request.form['setor']

        token = secrets.token_urlsafe(32)

        nova_avaliacao = AvaliacaoPsicossocial(
            cliente_id=cliente.id,
            nome_funcionario=nome,
            email_funcionario=email,
            cargo=cargo,
            setor=setor,
            token=token,
            status='pendente'
        )
        db.session.add(nova_avaliacao)
        db.session.commit()

        # Gera o link público da avaliação (usa o domínio da requisição)
        link_avaliacao = url_for('responder_avaliacao', token=token, _external=True)

        # Prepara o número de telefone
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        if not telefone_limpo.startswith('55'):
            telefone_limpo = '55' + telefone_limpo

        # Mensagem
        mensagem = f"Olá {nome}, você foi convidado para responder a avaliação psicossocial. Acesse o link: {link_avaliacao}"
        mensagem_codificada = quote(mensagem, safe='')
        link_whatsapp = f"https://wa.me/{telefone_limpo}?text={mensagem_codificada}"

        # Página com os links (azul, para copiar)
        return render_template('link_whatsapp_enviar.html',
                               link_whatsapp=link_whatsapp,
                               link_avaliacao=link_avaliacao,
                               nome_funcionario=nome)

    return render_template('nova_avaliacao_psicossocial.html', cliente=cliente)
@app.route('/avaliacao/link/<int:id>')
@login_required
def mostrar_link_avaliacao(id):
    avaliacao = db.session.get(AvaliacaoPsicossocial, id)
    if not avaliacao:
        flash('Avaliação não encontrada', 'danger')
        return redirect(url_for('listar_avaliacoes'))

    link = url_for('responder_avaliacao', token=avaliacao.token, _external=True)

    # Gera QR Code (opcional)
    try:
        import qrcode
        from io import BytesIO
        import base64

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        qr_code = f"data:image/png;base64,{qr_base64}"
    except:
        qr_code = None

    return render_template('mostrar_link.html',
                           avaliacao=avaliacao,
                           link=link,
                           qr_code=qr_code)




@app.route('/avaliacao/enviar/<int:id>')
@login_required
def reenviar_link_avaliacao(id):
    avaliacao = db.session.get(AvaliacaoPsicossocial, id)
    if not avaliacao:
        flash('Avaliação não encontrada', 'danger')
        return redirect(url_for('listar_avaliacoes'))

    cliente = db.session.get(Cliente, avaliacao.cliente_id)
    enviar_link_avaliacao(avaliacao, cliente)
    flash(f'Link reenviado para {avaliacao.email_funcionario}', 'success')
    return redirect(url_for('listar_avaliacoes'))


def enviar_link_avaliacao(avaliacao, cliente):
    link = url_for('responder_avaliacao', token=avaliacao.token, _external=True)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Avaliação Psicossocial</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 20px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Avaliação Psicossocial</h2>
            </div>
            <div class="content">
                <h3>Olá {avaliacao.nome_funcionario},</h3>
                <p>A empresa <strong>{cliente.empresa or cliente.nome}</strong> solicitou sua participação na avaliação psicossocial.</p>
                <p><strong>Cargo:</strong> {avaliacao.cargo}<br>
                <strong>Setor:</strong> {avaliacao.setor}</p>
                <p>Por favor, clique no botão abaixo para responder o questionário:</p>
                <p style="text-align: center;">
                    <a href="{link}" class="button">Responder Avaliação</a>
                </p>
                <p>Este link é único e válido para uma única resposta.</p>
                <p><small>Se o botão não funcionar, copie e cole o link abaixo:</small></p>
                <p><small>{link}</small></p>
            </div>
            <div class="footer">
                <p>Este é um email automático, por favor não responda.</p>
                <p>Sistema SST - Gerenciamento de Riscos Ocupacionais</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        from flask_mail import Message
        msg = Message(
            subject=f"Avaliação Psicossocial - {avaliacao.nome_funcionario}",
            recipients=[avaliacao.email_funcionario],
            html=html_content
        )
        mail.send(msg)
        avaliacao.email_enviado = True
        avaliacao.data_envio = datetime.now()
        db.session.commit()
        print(f"✅ Email enviado para {avaliacao.email_funcionario}")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")


@app.route('/avaliacao/responder/<token>', methods=['GET', 'POST'])
def responder_avaliacao(token):
    avaliacao = AvaliacaoPsicossocial.query.filter_by(token=token, status='pendente').first()

    if not avaliacao:
        flash('Link inválido ou questionário já respondido!', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Coleta as respostas
        respostas = {}
        for key, value in request.form.items():
            if key.startswith('q'):
                respostas[key] = int(value) if value.isdigit() else value

        # Calcula pontuação
        pontuacao_total = sum([int(v) for v in respostas.values() if isinstance(v, int)])

        # Determina nível de risco
        if pontuacao_total <= 20:
            nivel_risco = 'Baixo'
        elif pontuacao_total <= 35:
            nivel_risco = 'Médio'
        elif pontuacao_total <= 50:
            nivel_risco = 'Alto'
        else:
            nivel_risco = 'Crítico'

        import json
        avaliacao.respostas = json.dumps(respostas, ensure_ascii=False)
        avaliacao.pontuacao_total = pontuacao_total
        avaliacao.nivel_risco = nivel_risco
        avaliacao.status = 'respondido'
        avaliacao.data_resposta = datetime.now()
        db.session.commit()

        flash('Avaliação concluída com sucesso!', 'success')
        return redirect(url_for('ver_resultado', id=avaliacao.id))

    return render_template('questionario_psicossocial.html', avaliacao=avaliacao)


@app.route('/avaliacao/resultado/<int:id>')
def ver_resultado(id):
    avaliacao = db.session.get(AvaliacaoPsicossocial, id)
    if not avaliacao:
        flash('Avaliação não encontrada', 'danger')
        return redirect(url_for('index'))

    return render_template('resultado_avaliacao.html', avaliacao=avaliacao)


from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from flask import send_file
import json
from datetime import datetime


@app.route('/avaliacao/pdf/<int:avaliacao_id>')
@login_required
def gerar_pdf_resultado(avaliacao_id):
    avaliacao = AvaliacaoPsicossocial.query.get_or_404(avaliacao_id)

    # Carregar respostas (JSON)
    respostas = {}
    if avaliacao.respostas:
        try:
            respostas = json.loads(avaliacao.respostas)
        except:
            respostas = {"Erro": "Não foi possível carregar as respostas"}

    # Calcular pontuação (assumindo valores 1 a 5)
    pontuacao_total = 0
    for pergunta, resposta in respostas.items():
        if isinstance(resposta, (int, float)):
            pontuacao_total += resposta
        elif isinstance(resposta, str) and resposta.isdigit():
            pontuacao_total += int(resposta)

    # Diagnóstico
    if pontuacao_total <= 10:
        diagnostico = "Baixo risco psicossocial. Ambiente saudável."
    elif pontuacao_total <= 20:
        diagnostico = "Risco moderado. Recomenda-se acompanhamento."
    else:
        diagnostico = "Alto risco psicossocial. Ações imediatas necessárias."

    # Criar PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "RELATÓRIO DE AVALIAÇÃO PSICOSSOCIAL")
    y -= 40

    # Dados do funcionário
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Funcionário: {avaliacao.nome_funcionario}")
    y -= 20
    c.drawString(50, y,
                 f"Data: {avaliacao.data_resposta.strftime('%d/%m/%Y %H:%M') if avaliacao.data_resposta else datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 20
    c.drawString(50, y, f"Cargo: {avaliacao.cargo} | Setor: {avaliacao.setor}")
    y -= 30

    # Pontuação e diagnóstico
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Pontuação total: {pontuacao_total} pontos")
    y -= 20
    c.drawString(50, y, f"Diagnóstico: {diagnostico}")
    y -= 40

    # Detalhamento das respostas
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Respostas detalhadas:")
    y -= 20
    c.setFont("Helvetica", 10)

    for pergunta, resposta in respostas.items():
        texto = f"• {pergunta}: {resposta}"
        linhas = simpleSplit(texto, c._fontname, c._fontsize, width - 100)
        for linha in linhas:
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)
            c.drawString(50, y, linha)
            y -= 15
        y -= 5

    # Rodapé na última página
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=False,
        mimetype='application/pdf',
        download_name=f'resultado_avaliacao_{avaliacao_id}.pdf'
    )
@app.route('/avaliacoes')
@login_required
def listar_avaliacoes():
    # Ordenar por data_envio decrescente (mais recente primeiro)
    avaliacoes = AvaliacaoPsicossocial.query.order_by(AvaliacaoPsicossocial.data_envio.desc()).all()
    return render_template('avaliacoes_list.html', avaliacoes=avaliacoes)

@app.route('/avaliacao/short/<token>')
def avaliacao_short(token):
    return redirect(url_for('responder_avaliacao', token=token))
from flask import send_file

def gerar_pdf_resultado(avaliacao_id):
    avaliacao = AvaliacaoPsicossocial.query.get_or_404(avaliacao_id)
    # Recupera as respostas (assumindo que estão em JSON)
    import json
    respostas = json.loads(avaliacao.respostas) if avaliacao.respostas else {}
    pontuacao_total = sum(int(v) for v in respostas.values() if v.isdigit())
    # Agora use pontuacao_total no PDF
    p.drawString(50, y, f"PONTUAÇÃO TOTAL: {pontuacao_total} pontos")

import requests

def encurtar_url(url):
    try:
        response = requests.get(f"https://tinyurl.com/api-create.php?url={url}")
        if response.status_code == 200:
            return response.text
    except:
        pass
    return url
@app.route('/avaliacao/excluir/<int:avaliacao_id>', methods=['POST'])
@login_required
def excluir_avaliacao(avaliacao_id):
    avaliacao = AvaliacaoPsicossocial.query.get_or_404(avaliacao_id)
    db.session.delete(avaliacao)
    db.session.commit()
    flash('Avaliação excluída com sucesso!', 'success')
    return redirect(url_for('listar_avaliacoes'))
########################################################   ROTAS DE EPI ####################################
# Importações necessárias (certifique-se de que todas estão no topo do arquivo)
from flask import render_template, make_response, redirect, url_for, flash, request
from flask_login import login_required
from datetime import datetime
from models import EPIEntrega, Funcionario  # ajuste o caminho conforme seu projeto

# ================== ROTAS CORRIGIDAS ==================

@app.route('/listar_epi')
@login_required
def listar_epi():
    try:
        entregas = EPIEntrega.query.all()
        # Adiciona o nome do funcionário ao objeto (para exibição no template)
        for entrega in entregas:
            entrega.funcionario_nome = entrega.funcionario.nome if entrega.funcionario else 'Desconhecido'
    except Exception as e:
        entregas = []
        flash('Erro ao carregar EPIs. Verifique se a tabela existe.', 'warning')
    return render_template('listar_epi.html', entregas=entregas)


@app.route('/criar_entrega_epi', methods=['GET', 'POST'])
@login_required
def criar_entrega_epi():
    if request.method == 'POST':
        funcionario_id = request.form.get('funcionario_id')
        epi_nome = request.form.get('epi_nome')
        quantidade = int(request.form.get('quantidade', 1))
        data_entrega = datetime.strptime(request.form.get('data_entrega'), '%Y-%m-%d').date()
        data_validade = request.form.get('data_validade')
        if data_validade:
            data_validade = datetime.strptime(data_validade, '%Y-%m-%d').date()
        else:
            data_validade = None
        observacoes = request.form.get('observacoes')

        nova_entrega = EPIEntrega(
            funcionario_id=funcionario_id,
            epi_nome=epi_nome,
            quantidade=quantidade,
            data_entrega=data_entrega,
            data_validade=data_validade,
            observacoes=observacoes
        )
        db.session.add(nova_entrega)
        db.session.commit()
        flash('Entrega de EPI registrada com sucesso!', 'success')
        return redirect(url_for('listar_epi'))

    funcionarios = Funcionario.query.all()
    return render_template('criar_entrega_epi.html', funcionarios=funcionarios)


# ROTA DA FICHA (SEM WEYASPRINT – usa HTML + impressão do navegador)
@app.route('/ficha_epi/<int:entrega_id>')
@login_required
def ficha_epi(entrega_id):
    entrega = EPIEntrega.query.get_or_404(entrega_id)
    funcionario = entrega.funcionario
    # Tenta obter a empresa associada ao funcionário (se existir)
    empresa = None
    if funcionario and hasattr(funcionario, 'empresa'):
        empresa = funcionario.empresa
    elif funcionario and hasattr(funcionario, 'empresa_id'):
        # Se houver relacionamento, busque a empresa
        from models import Empresa
        empresa = Empresa.query.get(funcionario.empresa_id) if funcionario.empresa_id else None

    return render_template('ficha_epi_pdf.html',
                           entrega=entrega,
                           funcionario=funcionario,
                           empresa=empresa,
                           data_atual=datetime.now().strftime('%d/%m/%Y %H:%M'))
with app.app_context():
    db.create_all()
    print("✅ Tabelas verificadas/criadas com sucesso!")

################################################################# RECUPERAÇÃO DE SENHA ########################
import random
import string


@app.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            flash('Digite o nome de usuário', 'danger')
            return redirect(url_for('esqueci_senha'))

        user = User.query.filter_by(username=username).first()
        if not user:
            # Por segurança, não informa se usuário existe (mas para simplificar, pode avisar)
            flash('Usuário não encontrado', 'danger')
            return redirect(url_for('esqueci_senha'))

        # Gerar senha temporária (6 caracteres alfanuméricos)
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        user.set_password(temp_password)  # método que faz hash
        db.session.commit()

        # Exibe a senha na tela (sem e-mail)
        return render_template('senha_temporaria.html', senha=temp_password, username=user.username)

    return render_template('esqueci_senha.html')
# ================= EXECUÇÃO =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
