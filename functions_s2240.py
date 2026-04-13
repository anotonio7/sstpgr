# functions_s2240.py
from datetime import datetime
from xml.dom import minidom

def gerar_xml_s2240(evento, empresa, funcionario, versao='2'):
    """Gera XML do evento S-2240 (Condições Ambientais de Trabalho)"""
    try:
        # Dados da empresa
        cnpj_empresa = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
        
        # Dados do funcionário
        cpf_trab = funcionario.cpf.replace('.', '').replace('-', '')
        matricula = getattr(funcionario, 'matricula_esocial', '') or '000001'
        
        # Dados do evento
        data_avaliacao = evento.data_avaliacao.strftime('%Y-%m-%d')
        cpf_avaliador = evento.cpf_avaliador.replace('.', '').replace('-', '')
        
        # Gera XML
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtMonit/v_S_01_02_00">
    <evtMonit Id="ID{cnpj_empresa}{data_avaliacao.replace("-", "")}0001">
        <ideEvento>
            <indRetificacao>1</indRetificacao>
            <nrRecibo></nrRecibo>
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
        <infoMonit>
            <dtAvaliacao>{data_avaliacao}</dtAvaliacao>
            <cpfAvaliador>{cpf_avaliador}</cpfAvaliador>
        </infoMonit>
    </evtMonit>
</eSocial>'''
        
        # Formata o XML
        dom = minidom.parseString(xml)
        xml_formatado = dom.toprettyxml(indent="  ")
        
        # Remove a primeira linha se for declaração XML
        linhas = xml_formatado.split('\n')
        if linhas and linhas[0].startswith('<?xml'):
            xml_final = '\n'.join(linhas[1:])
        else:
            xml_final = xml_formatado
            
        return xml_final.strip()
        
    except Exception as e:
        print(f"Erro ao gerar XML S-2240: {e}")
        import traceback
        traceback.print_exc()
        return ""

def gerar_xml_s2240_completo(evento):
    """Versão alternativa que aceita apenas o evento"""
    return gerar_xml_s2240(evento, evento.funcionario.empresa, evento.funcionario)
