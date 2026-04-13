# functions_s2221.py
from datetime import datetime
from xml.dom import minidom

def gerar_xml_s2221(evento, empresa, funcionario):
    """Gera XML do evento S-2221 (Exame Toxicológico)"""
    try:
        cnpj_empresa = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
        cpf_trab = funcionario.cpf.replace('.', '').replace('-', '')
        matricula = getattr(funcionario, 'matricula_esocial', '') or '000001'
        
        data_exame = evento.data_exame.strftime('%Y-%m-%d') if hasattr(evento, 'data_exame') else datetime.now().strftime('%Y-%m-%d')
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtExameTox/v_S_01_02_00">
    <evtExameTox Id="ID{cnpj_empresa}{datetime.now().strftime('%Y%m%d%H%M%S')}">
        <ideEvento>
            <tpAmb>2</tpAmb>
            <procEmi>1</procEmi>
            <verProc>1.0</verProc>
        </ideEvento>
        <ideEmpregador>
            <tpInsc>1</tpInsc>
            <nrInsc>{cnpj_empresa}</nrInsc>
        </ideEmpregador>
        <ideVinculo>
            <cpfTrab>{cpf_trab}</cpfTrab>
            <matricula>{matricula}</matricula>
        </ideVinculo>
        <exameTox>
            <dtExame>{data_exame}</dtExame>
        </exameTox>
    </evtExameTox>
</eSocial>'''
        
        dom = minidom.parseString(xml)
        xml_formatado = dom.toprettyxml(indent="  ")
        linhas = xml_formatado.split('\n')
        if linhas and linhas[0].startswith('<?xml'):
            return '\n'.join(linhas[1:]).strip()
        return xml_formatado.strip()
    except Exception as e:
        print(f"Erro ao gerar XML S-2221: {e}")
        return ""

def gerar_xml_s2221_completo(evento):
    return gerar_xml_s2221(evento, evento.funcionario.empresa, evento.funcionario)