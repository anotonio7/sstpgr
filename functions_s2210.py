# functions_s2210.py
from datetime import datetime
from xml.dom import minidom

def gerar_xml_s2210(evento, empresa, funcionario):
    """Gera XML do evento S-2210 (CAT)"""
    try:
        cnpj_empresa = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
        cpf_trab = funcionario.cpf.replace('.', '').replace('-', '')
        matricula = getattr(funcionario, 'matricula_esocial', '') or '000001'
        
        data_acidente = evento.data_acidente.strftime('%Y-%m-%d') if hasattr(evento, 'data_acidente') else datetime.now().strftime('%Y-%m-%d')
        hora_acidente = getattr(evento, 'hora_acidente', '12:00')
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtCAT/v_S_01_02_00">
    <evtCAT Id="ID{cnpj_empresa}{datetime.now().strftime('%Y%m%d%H%M%S')}">
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
        <cat>
            <dtAcidente>{data_acidente}</dtAcidente>
            <hrAcidente>{hora_acidente}</hrAcidente>
        </cat>
    </evtCAT>
</eSocial>'''
        
        dom = minidom.parseString(xml)
        xml_formatado = dom.toprettyxml(indent="  ")
        linhas = xml_formatado.split('\n')
        if linhas and linhas[0].startswith('<?xml'):
            return '\n'.join(linhas[1:]).strip()
        return xml_formatado.strip()
    except Exception as e:
        print(f"Erro ao gerar XML S-2210: {e}")
        return ""

def gerar_xml_s2210_completo(evento):
    return gerar_xml_s2210(evento, evento.funcionario.empresa, evento.funcionario)