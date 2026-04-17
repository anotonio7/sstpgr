from flask_wtf import FlaskForm
from wtforms import DateField, StringField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional

class S2220Form(FlaskForm):
    data_avaliacao = DateField('Data da Avaliação', validators=[DataRequired()], format='%Y-%m-%d')
    cpf_avaliador = StringField('CPF do Avaliador', validators=[DataRequired()])
    nenhum_risco = BooleanField('Nenhum risco identificado', default=False)
    # Se houver outros campos, adicione aqui

# Se você também usa o formulário de exame (S2220ExameForm), inclua abaixo:
class S2220ExameForm(FlaskForm):
    data_exame = DateField('Data do Exame', validators=[DataRequired()], format='%Y-%m-%d')
    tipo_exame = SelectField('Tipo de Exame', choices=[
        ('ADMISSIONAL', 'Admissional'),
        ('PERIODICO', 'Periódico'),
        ('RETORNO', 'Retorno ao Trabalho'),
        ('MUDANCA', 'Mudança de Função'),
        ('DEMISSIONAL', 'Demissional')
    ], validators=[DataRequired()])
    resultado = TextAreaField('Resultado do Exame', validators=[DataRequired()])
    descricao_atividade = TextAreaField('Descrição da Atividade', validators=[Optional()], render_kw={'rows': 3})