from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
from flask import send_file

def gerar_pdf_s2220(evento):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Evento S-2220 {evento.id}")
    styles = getSampleStyleSheet()
    story = []

    # Título
    titulo = Paragraph(f"Evento S-2220 - Monitoramento da Saúde", styles['Title'])
    story.append(titulo)
    story.append(Spacer(1, 0.5*cm))

    # Dados do funcionário
    func = evento.funcionario
    dados_func = [
        ["Funcionário:", func.nome],
        ["CPF:", func.cpf],
        ["Matrícula eSocial:", func.matricula_esocial or "não informada"],
        ["Empresa:", func.empresa.nome if func.empresa else "-"],
    ]
    t = Table(dados_func, colWidths=[4*cm, 10*cm])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Dados do exame
    dados_exame = [
        ["Data do Exame:", evento.data_exame.strftime('%d/%m/%Y')],
        ["Tipo de Exame:", evento.tipo_exame],
        ["Resultado:", evento.resultado],
        ["CRM Médico:", evento.crm_medico],
        ["UF CRM:", evento.uf_crm],
    ]
    t2 = Table(dados_exame, colWidths=[4*cm, 10*cm])
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t2)

    # Status e recibo (se houver)
    if evento.recibo:
        story.append(Spacer(1, 0.5*cm))
        recibo_par = Paragraph(f"<b>Recibo de envio:</b><br/>{evento.recibo}", styles['Normal'])
        story.append(recibo_par)

    # Constroi o PDF
    doc.build(story)
    buffer.seek(0)
    return buffer