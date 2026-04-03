
import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from models import db, Empresa, Funcionario, EventoS2220, EventoS2221, EventoS2210, EventoS2240, ConfigCertificado
from esocial_utils import (
    carregar_certificado, assinar_xml, gerar_xml_s2220, gerar_xml_s2221,
    gerar_xml_s2210, gerar_xml_s2240, enviar_lote
)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
from flask import send_file
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from models import Empresa, Funcionario, EventoS2220, S2220Exame, EventoS2221, EventoS2210, EventoS2240, ConfigCertificado
from flask import Flask, send_file
from models import EventoS2220   # ← nome correto
from io import BytesIO
from flask import send_file
from flask import send_file
from flask import session, request, flash, redirect, url_for, render_template
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sst2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'certs')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


db.init_app(app)

# ================= LOGIN =================
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        login_user(User(1))
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ================= DASHBOARD =================

def gerar_pdf_s2220(evento):
    """
    Gera um PDF profissional para o evento S-2220 (ASO)
    com bordas laterais e layout aprimorado.
    """

    # ------------------------------------------------------------
    # 1. Classe personalizada para desenhar bordas laterais em cada página
    # ------------------------------------------------------------
    class BorderedDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kw):
            super().__init__(filename, **kw)
            # Cria um frame que cobre toda a área útil (já descontadas as margens)
            frame = Frame(
                self.leftMargin, self.bottomMargin,
                self.width, self.height,
                id='normal'
            )
            # Adiciona um page template que, antes de desenhar o conteúdo, desenha as bordas
            template = PageTemplate(
                id='Bordered',
                frames=[frame],
                onPage=self._draw_borders
            )
            self.addPageTemplates([template])

        def _draw_borders(self, canvas, doc):
            """Desenha bordas laterais (esquerda e direita) e opcionalmente superior/inferior."""
            canvas.saveState()
            # Borda esquerda
            canvas.setStrokeColor(colors.HexColor('#003366'))
            canvas.setLineWidth(2)
            canvas.line(
                doc.leftMargin - 5, doc.bottomMargin - 5,
                doc.leftMargin - 5, doc.height + doc.bottomMargin + 5
            )
            # Borda direita
            canvas.line(
                doc.leftMargin + doc.width + 5, doc.bottomMargin - 5,
                doc.leftMargin + doc.width + 5, doc.height + doc.bottomMargin + 5
            )
            # Opcional: bordas superior e inferior (linhas finas)
            canvas.setStrokeColor(colors.grey)
            canvas.setLineWidth(0.5)
            # Superior
            canvas.line(
                doc.leftMargin - 5, doc.height + doc.bottomMargin + 5,
                doc.leftMargin + doc.width + 5, doc.height + doc.bottomMargin + 5
            )
            # Inferior
            canvas.line(
                doc.leftMargin - 5, doc.bottomMargin - 5,
                doc.leftMargin + doc.width + 5, doc.bottomMargin - 5
            )
            canvas.restoreState()

    # ------------------------------------------------------------
    # 2. Configuração do documento com margens reduzidas e template com bordas
    # ------------------------------------------------------------
    buffer = BytesIO()
    doc = BorderedDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm,
        topMargin=2.2*cm,
        bottomMargin=2.0*cm
    )
    styles = getSampleStyleSheet()
    story = []

    # Estilos aprimorados
    titulo_style = ParagraphStyle(
        'TituloGrande',
        parent=styles['Title'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.HexColor('#003366'),
        fontName='Helvetica-Bold'
    )
    subtitulo_style = ParagraphStyle(
        'Subtitulo',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4F4F4F'),
        spaceAfter=24,
        fontName='Helvetica'
    )
    heading_style = ParagraphStyle(
        'HeadingCustom',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#003366'),
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        fontName='Helvetica-Bold'
    )

    # ------------------------------------------------------------
    # 3. Cabeçalho visual (linha decorativa)
    # ------------------------------------------------------------
    story.append(Paragraph("Atestado de Saúde Ocupacional - ASO", titulo_style))
    story.append(Paragraph("Evento S-2220 - Monitoramento da Saúde do Trabalhador", subtitulo_style))
    story.append(Spacer(1, 0.2*cm))

    # ------------------------------------------------------------
    # 4. Função auxiliar para criar tabelas padronizadas
    # ------------------------------------------------------------
    def criar_tabela(dados, largura_col1=3.5*cm, largura_col2=12*cm):
        tabela = Table(dados, colWidths=[largura_col1, largura_col2])
        tabela.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#CCCCCC')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#E6F0FA')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        return tabela

    # ------------------------------------------------------------
    # 5. Dados da empresa
    # ------------------------------------------------------------
    func = evento.funcionario
    empresa = func.empresa if hasattr(func, 'empresa') else None

    dados_empresa = [
        ["Empregador:", empresa.nome if empresa else "-"],
        ["CNPJ:", empresa.cnpj if empresa else "-"],
        ["Endereço:", f"{empresa.rua}, {empresa.bairro}, {empresa.cidade}/{empresa.estado} - CEP {empresa.cep}" if empresa else "-"],
    ]
    story.append(criar_tabela(dados_empresa))
    story.append(Spacer(1, 0.4*cm))

    # ------------------------------------------------------------
    # 6. Dados do funcionário
    # ------------------------------------------------------------
    dados_func = [
        ["Funcionário:", func.nome if hasattr(func, 'nome') else "-"],
        ["CPF:", func.cpf if hasattr(func, 'cpf') else "-"],
        ["Matrícula eSocial:", func.matricula_esocial if hasattr(func, 'matricula_esocial') else "não informada"],
        ["Data de Nascimento:", func.nascimento.strftime('%d/%m/%Y') if hasattr(func, 'nascimento') and func.nascimento else "-"],
        ["Data de Admissão:", func.admissao.strftime('%d/%m/%Y') if hasattr(func, 'admissao') and func.admissao else "-"],
        ["Função/Cargo:", func.funcao if hasattr(func, 'funcao') else "-"],
    ]
    story.append(criar_tabela(dados_func))
    story.append(Spacer(1, 0.4*cm))

    # ------------------------------------------------------------
    # 7. Dados do evento (ASO)
    # ------------------------------------------------------------
    dados_aso = [
        ["Data do ASO:", evento.data_aso.strftime('%d/%m/%Y') if evento.data_aso else "-"],
        ["Médico (CRM):", f"{evento.crm_medico} / {evento.uf_crm}" if evento.crm_medico else "-"],
        ["Status:", evento.status if evento.status else "-"],
        ["Data de envio ao eSocial:", evento.data_envio.strftime('%d/%m/%Y %H:%M') if evento.data_envio else "-"],
    ]
    story.append(criar_tabela(dados_aso))
    story.append(Spacer(1, 0.6*cm))

    # ------------------------------------------------------------
    # 8. Tabela de exames (com estilo melhorado)
    # ------------------------------------------------------------
    if hasattr(evento, 'exames') and evento.exames:
        story.append(Paragraph("Exames Realizados", heading_style))
        story.append(Spacer(1, 0.2*cm))

        exames_data = [["Data", "Tipo de Exame", "Resultado"]]
        for ex in evento.exames:
            exames_data.append([
                ex.data_exame.strftime('%d/%m/%Y') if hasattr(ex, 'data_exame') and ex.data_exame else "-",
                ex.tipo_exame if hasattr(ex, 'tipo_exame') else "-",
                Paragraph(ex.resultado.replace('\n', '<br/>') if hasattr(ex, 'resultado') and ex.resultado else "-", styles['Normal'])
            ])

        t_exames = Table(exames_data, colWidths=[3*cm, 4*cm, 8.5*cm])
        t_exames.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#CCCCCC')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_exames)
        story.append(Spacer(1, 0.8*cm))

    # ------------------------------------------------------------
    # 9. Assinaturas (alinhadas e com linhas)
    # ------------------------------------------------------------
    ass_style = ParagraphStyle('Assinatura', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, spaceBefore=6)
    story.append(Paragraph(f"Médico responsável: {evento.crm_medico} / {evento.uf_crm}", ass_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("_________________________", ass_style))
    story.append(Paragraph("Assinatura do funcionário", ass_style))

    # ------------------------------------------------------------
    # 10. Rodapé da página (opcional: número da página é adicionado automaticamente pelo template)
    # ------------------------------------------------------------
    # (O template BorderedDocTemplate já desenha as bordas laterais.
    #  O número da página pode ser adicionado com um frame extra, mas por simplicidade fica assim.)

    # ------------------------------------------------------------
    # 11. Construção do PDF
    # ------------------------------------------------------------
    doc.build(story)
    buffer.seek(0)
    return buffer
################################################################## inicio das Rotas #####################
@app.route('/')
@login_required
def home():
    empresas = Empresa.query.count()
    funcionarios = Funcionario.query.count()
    s2220 = EventoS2220.query.count()
    s2221 = EventoS2221.query.count()
    s2210 = EventoS2210.query.count()
    s2240 = EventoS2240.query.count()
    return render_template('dashboard.html',
        empresas=empresas,
        funcionarios=funcionarios,
        s2220=s2220, s2221=s2221, s2210=s2210, s2240=s2240,
        empresas_lista=Empresa.query.order_by(Empresa.id.desc()).limit(5).all(),
        funcionarios_lista=Funcionario.query.order_by(Funcionario.id.desc()).limit(5).all()
    )

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

@app.route('/empresa/create', methods=['GET','POST'])
@login_required
def create_empresa():
    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form['cnpj']
        cep = request.form['cep']
        endereco = buscar_endereco_por_cep(cep) if cep else None
        e = Empresa(
            nome=nome,
            cnpj=cnpj,
            cep=cep,
            rua=endereco.get('rua') if endereco else '',
            bairro=endereco.get('bairro') if endereco else '',
            cidade=endereco.get('cidade') if endereco else '',
            estado=endereco.get('estado') if endereco else ''
        )
        db.session.add(e)
        db.session.commit()
        flash('Empresa criada com sucesso!')
        return redirect(url_for('list_empresas'))
    return render_template('empresa/create.html')

@app.route('/empresa/edit/<int:id>', methods=['GET','POST'])
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

@app.route('/funcionario/create', methods=['GET','POST'])
@login_required
def create_funcionario():
    empresas = Empresa.query.all()
    if request.method == 'POST':
        f = Funcionario(
            nome=request.form['nome'],
            cpf=request.form['cpf'],
            matricula_esocial=request.form.get('matricula_esocial'),
            funcao=request.form['funcao'],
            nascimento=datetime.strptime(request.form['nascimento'], '%Y-%m-%d') if request.form.get('nascimento') else None,
            admissao=datetime.strptime(request.form['admissao'], '%Y-%m-%d') if request.form.get('admissao') else None,
            empresa_id=request.form['empresa_id']
        )
        db.session.add(f)
        db.session.commit()
        flash('Funcionário criado!')
        return redirect(url_for('list_funcionarios'))
    return render_template('funcionario/create.html', empresas=empresas)

@app.route('/funcionario/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_funcionario(id):
    f = Funcionario.query.get_or_404(id)
    empresas = Empresa.query.all()
    if request.method == 'POST':
        f.nome = request.form['nome']
        f.cpf = request.form['cpf']
        f.matricula_esocial = request.form.get('matricula_esocial')
        f.funcao = request.form['funcao']
        f.nascimento = datetime.strptime(request.form['nascimento'], '%Y-%m-%d') if request.form.get('nascimento') else None
        f.admissao = datetime.strptime(request.form['admissao'], '%Y-%m-%d') if request.form.get('admissao') else None
        f.empresa_id = request.form['empresa_id']
        db.session.commit()
        flash('Funcionário atualizado!')
        return redirect(url_for('list_funcionarios'))
    return render_template('funcionario/edit.html', f=f, empresas=empresas)

@app.route('/funcionario/delete/<int:id>')
@login_required
def delete_funcionario(id):
    f = Funcionario.query.get_or_404(id)
    db.session.delete(f)
    db.session.commit()
    flash('Funcionário excluído!')
    return redirect(url_for('list_funcionarios'))

# ================= EVENTO S-2220 =================
@app.route('/s2220/list')
@login_required
def list_s2220():
    eventos = EventoS2220.query.all()
    return render_template('eventos/s2220_list.html', eventos=eventos)

@app.route('/s2220/create', methods=['GET','POST'])
@login_required
def create_s2220():
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        # Cria o evento principal
        evento = EventoS2220(
            funcionario_id=request.form['funcionario_id'],
            data_aso=datetime.strptime(request.form['data_aso'], '%Y-%m-%d') if request.form.get('data_aso') else None,
            crm_medico=request.form['crm_medico'],
            uf_crm=request.form['uf_crm']
        )
        db.session.add(evento)
        db.session.flush()  # para obter o id do evento antes de adicionar os exames

        # Pega os arrays dos exames
        datas = request.form.getlist('data_exame[]')
        tipos = request.form.getlist('tipo_exame[]')
        resultados = request.form.getlist('resultado[]')

        for i in range(len(datas)):
            if datas[i] and tipos[i] and resultados[i]:
                exame = S2220Exame(
                    evento_id=evento.id,
                    data_exame=datetime.strptime(datas[i], '%Y-%m-%d'),
                    tipo_exame=tipos[i],
                    resultado=resultados[i]
                )
                db.session.add(exame)

        db.session.commit()
        flash('Evento S-2220 criado com sucesso!')
        return redirect(url_for('list_s2220'))
    return render_template('eventos/s2220_create.html', funcionarios=funcionarios)
@app.route('/s2220/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        evento.funcionario_id = request.form['funcionario_id']
        evento.data_exame = datetime.strptime(request.form['data_exame'], '%Y-%m-%d')
        evento.tipo_exame = request.form['tipo_exame']
        evento.resultado = request.form['resultado']
        evento.crm_medico = request.form['crm_medico']
        evento.uf_crm = request.form['uf_crm']
        db.session.commit()
        flash('Evento S-2220 atualizado!')
        return redirect(url_for('list_s2220'))
    return render_template('eventos/s2220_edit.html', evento=evento, funcionarios=funcionarios)

@app.route('/s2220/delete/<int:id>')
@login_required
def delete_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    flash('Evento S-2220 excluído!')
    return redirect(url_for('list_s2220'))

@app.route('/s2220/send/<int:id>')
@login_required
def send_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    if evento.status != 'pendente':
        flash('Este evento já foi enviado!')
        return redirect(url_for('list_s2220'))
    # Carregar certificado
    cfg = ConfigCertificado.query.first()
    if not cfg:
        flash('Configure o certificado digital antes de enviar!')
        return redirect(url_for('config_certificado'))
    try:
        cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
        # Gerar XML
        xml = gerar_xml_s2220(evento, evento.funcionario.empresa, evento.funcionario, cfg.ambiente)
        # Assinar
        xml_assinado = assinar_xml(xml, cert_pem, key_pem)
        # Enviar
        recibo = enviar_lote(xml_assinado, cfg.ambiente)
        evento.xml_enviado = xml_assinado
        evento.recibo = recibo
        evento.status = 'enviado'  # ou pode processar recibo para mudar para 'recebido'
        db.session.commit()
        flash('Evento enviado com sucesso!')
    except Exception as e:
        flash(f'Erro ao enviar: {str(e)}')
    return redirect(url_for('list_s2220'))

@app.route('/s2220/enviar/<int:id>', methods=['POST'])
def enviar_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    funcionario = evento.funcionario
    empresa = funcionario.empresa

    # 1. Gerar XML (ambiente homologação = '2')
    xml_str = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')

    # 2. Carregar certificado
    try:
        cert_pem, key_pem = carregar_certificado(CERT_PATH, CERT_PASS)
    except Exception as e:
        evento.status_envio = 'erro'
        evento.mensagem_erro = f"Falha no certificado: {str(e)}"
        db.session.commit()
        flash(f"Erro ao carregar certificado: {e}", 'danger')
        return redirect(url_for('list_s2220'))

    # 3. Assinar XML
    try:
        xml_assinado = assinar_xml(xml_str, cert_pem, key_pem)
    except Exception as e:
        evento.status_envio = 'erro'
        evento.mensagem_erro = f"Erro na assinatura: {str(e)}"
        db.session.commit()
        flash(f"Erro ao assinar XML: {e}", 'danger')
        return redirect(url_for('list_s2220'))

    # 4. Enviar para o eSocial
    try:
        resposta = enviar_lote(xml_assinado, ambiente='2')
    except Exception as e:
        evento.status_envio = 'erro'
        evento.mensagem_erro = f"Erro no envio: {str(e)}"
        db.session.commit()
        flash(f"Erro ao enviar: {e}", 'danger')
        return redirect(url_for('list_s2220'))

    # 5. Atualizar evento com sucesso
    evento.status_envio = 'enviado'
    evento.recibo = resposta          # salva o XML de resposta
    evento.data_envio = datetime.utcnow()
    db.session.commit()

    flash("Evento enviado com sucesso ao eSocial! Recibo salvo.", 'success')
    return redirect(url_for('list_s2220'))
@app.route('/s2220/download_xml/<int:id>')
def download_xml_s2220(id):
    evento = EventoS2220.query.get(id)
    if not evento:
        return "Evento não encontrado", 404
    funcionario = evento.funcionario
    empresa = funcionario.empresa
    # Gera o XML usando a função do esocial_utils
    from esocial_utils import gerar_xml_s2220
    xml_str = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')
    buffer = BytesIO(xml_str.encode('utf-8'))
    return send_file(
        buffer,
        download_name=f's2220_{evento.id}.xml',
        as_attachment=True,
        mimetype='application/xml'
    )
@app.route('/s2220/download_pdf/<int:id>')
def download_pdf_s2220(id):
    evento = EventoS2220.query.get(id)
    if not evento:
        return "Evento não encontrado", 404

    # Certifique-se de que a função gerar_pdf_s2220 está definida/importada
    # Se você a definiu em pdf_utils.py, importe: from pdf_utils import gerar_pdf_s2220
    # Ou se está no próprio main.py, use o nome correto.
    pdf_buffer = gerar_pdf_s2220(evento)   # ou gerar_pdf(evento) dependendo do nome
    if pdf_buffer is None:
        return "Erro ao gerar PDF", 500

    return send_file(
        pdf_buffer,
        download_name=f's2220_{evento.id}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )
@app.route('/s2220/view_xml/<int:id>')
def view_xml_s2220(id):
    evento = EventoS2220.query.get_or_404(id)
    funcionario = evento.funcionario
    empresa = funcionario.empresa
    xml_str = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')
    return Response(xml_str, mimetype='application/xml')
@app.route('/enviar_xml_manual', methods=['GET', 'POST'])
def enviar_xml_manual():
    # Verifica se o certificado está configurado
    if 'cert_data' not in session:
        flash('Configure o certificado digital antes de enviar!', 'warning')
        return redirect(url_for('config_cert'))

    if request.method == 'POST':
        # Recebe o arquivo XML
        xml_file = request.files.get('xml_file')
        if not xml_file or xml_file.filename == '':
            flash('Nenhum arquivo XML selecionado.', 'danger')
            return redirect(url_for('enviar_xml_manual'))

        # Lê o conteúdo do XML
        xml_content = xml_file.read().decode('utf-8')

        # Opcional: validar se é um XML bem formado
        try:
            ET.fromstring(xml_content)
        except ET.ParseError as e:
            flash(f'XML inválido: {str(e)}', 'danger')
            return redirect(url_for('enviar_xml_manual'))

        # Recupera certificado da sessão
        from esocial_utils import carregar_certificado_from_bytes
        try:
            cert_pem, key_pem = carregar_certificado_from_bytes(
                session['cert_data'],
                session['cert_pass']
            )
        except Exception as e:
            flash(f'Erro ao carregar certificado: {str(e)}', 'danger')
            return redirect(url_for('config_cert'))

        # Assina o XML
        try:
            xml_assinado = assinar_xml(xml_content, cert_pem, key_pem)
        except Exception as e:
            flash(f'Erro ao assinar XML: {str(e)}', 'danger')
            return redirect(url_for('enviar_xml_manual'))

        # Envia para o eSocial (ambiente configurado)
        ambiente = session.get('ambiente', '2')
        try:
            resposta = enviar_lote(xml_assinado, ambiente)
        except Exception as e:
            flash(f'Erro no envio: {str(e)}', 'danger')
            return redirect(url_for('enviar_xml_manual'))

        # Exibe o recibo (resposta do eSocial)
        flash('XML enviado com sucesso!', 'success')
        # Opção: mostrar o recibo em uma nova página ou modal
        return render_template('recibo.html', recibo=resposta)

    return render_template('enviar_xml_manual.html')
@app.route('/s2221/list')
@login_required
def list_s2221():
    eventos = EventoS2221.query.all()
    return render_template('eventos/s2221_list.html', eventos=eventos)

@app.route('/s2221/create', methods=['GET','POST'])
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

@app.route('/s2221/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_s2221(id):
    evento = EventoS2221.query.get_or_404(id)
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        evento.funcionario_id = request.form['funcionario_id']
        evento.data_exame = datetime.strptime(request.form['data_exame'], '%Y-%m-%d')
        evento.tipo_exame = request.form['tipo_exame']
        evento.resultado = request.form['resultado']
        evento.laboratorio = request.form.get('laboratorio')
        db.session.commit()
        flash('Evento S-2221 atualizado!')
        return redirect(url_for('list_s2221'))
    return render_template('eventos/s2221_edit.html', evento=evento, funcionarios=funcionarios)

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
@app.route('/s2210/list')
@login_required
def list_s2210():
    eventos = EventoS2210.query.all()
    return render_template('eventos/s2210_list.html', eventos=eventos)

@app.route('/s2210/create', methods=['GET','POST'])
@login_required
def create_s2210():
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        e = EventoS2210(
            funcionario_id=request.form['funcionario_id'],
            data_acidente=datetime.strptime(request.form['data_acidente'], '%Y-%m-%d'),
            tipo_acidente=request.form['tipo_acidente'],
            local=request.form.get('local'),
            parte_atingida=request.form.get('parte_atingida'),
            descricao=request.form['descricao']
        )
        db.session.add(e)
        db.session.commit()
        flash('Evento S-2210 criado!')
        return redirect(url_for('list_s2210'))
    return render_template('eventos/s2210_create.html', funcionarios=funcionarios)

@app.route('/s2210/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_s2210(id):
    evento = EventoS2210.query.get_or_404(id)
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        evento.funcionario_id = request.form['funcionario_id']
        evento.data_acidente = datetime.strptime(request.form['data_acidente'], '%Y-%m-%d')
        evento.tipo_acidente = request.form['tipo_acidente']
        evento.local = request.form.get('local')
        evento.parte_atingida = request.form.get('parte_atingida')
        evento.descricao = request.form['descricao']
        db.session.commit()
        flash('Evento S-2210 atualizado!')
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
        xml = gerar_xml_s2210(evento, evento.funcionario.empresa, evento.funcionario, cfg.ambiente)
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
@app.route('/s2240/list')
@login_required
def list_s2240():
    eventos = EventoS2240.query.all()
    return render_template('eventos/s2240_list.html', eventos=eventos)

@app.route('/s2240/create', methods=['GET','POST'])
@login_required
def create_s2240():
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        e = EventoS2240(
            funcionario_id=request.form['funcionario_id'],
            data_avaliacao=datetime.strptime(request.form['data_avaliacao'], '%Y-%m-%d'),
            agente_risco=request.form['agente_risco'],
            intensidade=request.form.get('intensidade'),
            epi_utilizado=request.form.get('epi_utilizado')
        )
        db.session.add(e)
        db.session.commit()
        flash('Evento S-2240 criado!')
        return redirect(url_for('list_s2240'))
    return render_template('eventos/s2240_create.html', funcionarios=funcionarios)

@app.route('/s2240/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_s2240(id):
    evento = EventoS2240.query.get_or_404(id)
    funcionarios = Funcionario.query.all()
    if request.method == 'POST':
        evento.funcionario_id = request.form['funcionario_id']
        evento.data_avaliacao = datetime.strptime(request.form['data_avaliacao'], '%Y-%m-%d')
        evento.agente_risco = request.form['agente_risco']
        evento.intensidade = request.form.get('intensidade')
        evento.epi_utilizado = request.form.get('epi_utilizado')
        db.session.commit()
        flash('Evento S-2240 atualizado!')
        return redirect(url_for('list_s2240'))
    return render_template('eventos/s2240_edit.html', evento=evento, funcionarios=funcionarios)

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
# Rotas similares para S-2221, S-2210, S-2240 (seguir o mesmo padrão)

# ================= CONFIGURAÇÃO DO CERTIFICADO =================
import os
from werkzeug.utils import secure_filename

@app.route('/config_cert', methods=['GET', 'POST'])
def config_cert():
    if request.method == 'POST':
        pfx_file = request.files['cert_file']
        senha = request.form['senha']
        ambiente = request.form['ambiente']
        if pfx_file:
            # Gera um nome único para o arquivo
            filename = secure_filename(f"cert_{datetime.utcnow().timestamp()}.pfx")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            pfx_file.save(filepath)
            # Armazena apenas o caminho e a senha na sessão
            session['cert_path'] = filepath
            session['cert_pass'] = senha
            session['ambiente'] = ambiente
            flash('Certificado configurado com sucesso!', 'success')
        else:
            flash('Nenhum arquivo enviado.', 'danger')
        return redirect(url_for('list_s2220'))
    return render_template('config_cert.html')


# ================= EXECUÇÃO =================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)