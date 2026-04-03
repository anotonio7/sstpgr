import os
import requests
from lxml import etree
from signxml import XMLSigner
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from datetime import datetime

# URLs dos webservices
WS_URL_HOMOLOG = "https://homologacao.esocial.gov.br/servico/evt/eventos"
WS_URL_PROD = "https://api.esocial.gov.br/servico/evt/eventos"

def carregar_certificado(cert_path, senha):
    """Carrega certificado PFX do arquivo e retorna (cert_pem, key_pem)"""
    with open(cert_path, 'rb') as f:
        pfx_data = f.read()
    return carregar_certificado_from_bytes(pfx_data, senha)

def carregar_certificado_from_bytes(pfx_bytes, senha):
    """Carrega certificado a partir de bytes (já lido do arquivo)"""
    private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_bytes, senha.encode())
    key_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    ).decode('utf-8')
    cert_pem = certificate.public_bytes(Encoding.PEM).decode('utf-8')
    return cert_pem, key_pem

def assinar_xml(xml_string, cert_pem, key_pem):
    """Assina o XML usando signxml"""
    root = etree.fromstring(xml_string.encode('utf-8'))
    signer = XMLSigner(method='rsa-sha256', c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#')
    signed_root = signer.sign(root, key=key_pem.encode(), cert=cert_pem.encode())
    return etree.tostring(signed_root, encoding='unicode')

def gerar_xml_s2220(evento, empresa, funcionario, ambiente='2'):
    """
    Gera XML do evento S-2220 (Monitoramento da Saúde - ASO)
    evento: objeto EventoS2220
    empresa: objeto Empresa
    funcionario: objeto Funcionario
    ambiente: '1'=produção, '2'=homologação
    """
    ns = "http://www.esocial.gov.br/schema/evt/evtMonit/v02_05_00"
    root = etree.Element("eSocial", xmlns=ns)
    evtMonit = etree.SubElement(root, "evtMonit")

    ideEvento = etree.SubElement(evtMonit, "ideEvento")
    etree.SubElement(ideEvento, "tpAmb").text = ambiente
    etree.SubElement(ideEvento, "procEmi").text = "1"
    etree.SubElement(ideEvento, "verProc").text = "1.0"

    ideEmpregador = etree.SubElement(evtMonit, "ideEmpregador")
    etree.SubElement(ideEmpregador, "tpInsc").text = "1"  # CNPJ
    cnpj_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
    etree.SubElement(ideEmpregador, "nrInsc").text = cnpj_limpo

    ideTrab = etree.SubElement(evtMonit, "ideTrab")
    cpf_limpo = funcionario.cpf.replace('.', '').replace('-', '')
    etree.SubElement(ideTrab, "cpfTrab").text = cpf_limpo

    # Dados do ASO
    aso = etree.SubElement(evtMonit, "aso")
    etree.SubElement(aso, "dtAso").text = evento.data_aso.strftime('%Y-%m-%d') if evento.data_aso else ''
    if evento.crm_medico:
        medico = etree.SubElement(aso, "medico")
        etree.SubElement(medico, "crmMedico").text = evento.crm_medico
        etree.SubElement(medico, "ufCRM").text = evento.uf_crm

    # Exames (se houver)
    if hasattr(evento, 'exames') and evento.exames:
        for exame in evento.exames:
            exame_elem = etree.SubElement(aso, "exame")
            if hasattr(exame, 'data_exame') and exame.data_exame:
                etree.SubElement(exame_elem, "dtExame").text = exame.data_exame.strftime('%Y-%m-%d')
            if hasattr(exame, 'tipo_exame') and exame.tipo_exame:
                etree.SubElement(exame_elem, "tpExame").text = exame.tipo_exame
            if hasattr(exame, 'resultado') and exame.resultado:
                etree.SubElement(exame_elem, "resExame").text = exame.resultado

    return etree.tostring(root, encoding='unicode', pretty_print=True)

def gerar_xml_s2221(evento, empresa, funcionario, ambiente='2'):
    """Gera XML do evento S-2221 (Exame Toxicológico)"""
    ns = "http://www.esocial.gov.br/schema/evt/evtToxicologico/v02_05_00"
    root = etree.Element("eSocial", xmlns=ns)
    evtTox = etree.SubElement(root, "evtToxicologico")

    ideEvento = etree.SubElement(evtTox, "ideEvento")
    etree.SubElement(ideEvento, "tpAmb").text = ambiente
    etree.SubElement(ideEvento, "procEmi").text = "1"
    etree.SubElement(ideEvento, "verProc").text = "1.0"

    ideEmpregador = etree.SubElement(evtTox, "ideEmpregador")
    etree.SubElement(ideEmpregador, "tpInsc").text = "1"
    cnpj_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
    etree.SubElement(ideEmpregador, "nrInsc").text = cnpj_limpo

    ideTrab = etree.SubElement(evtTox, "ideTrab")
    cpf_limpo = funcionario.cpf.replace('.', '').replace('-', '')
    etree.SubElement(ideTrab, "cpfTrab").text = cpf_limpo

    exame = etree.SubElement(evtTox, "exame")
    if hasattr(evento, 'data_exame') and evento.data_exame:
        etree.SubElement(exame, "dtExame").text = evento.data_exame.strftime('%Y-%m-%d')
    if hasattr(evento, 'tipo_exame') and evento.tipo_exame:
        etree.SubElement(exame, "tpExame").text = evento.tipo_exame
    if hasattr(evento, 'resultado') and evento.resultado:
        etree.SubElement(exame, "resExame").text = evento.resultado
    if hasattr(evento, 'laboratorio') and evento.laboratorio:
        etree.SubElement(exame, "nmLaboratorio").text = evento.laboratorio

    return etree.tostring(root, encoding='unicode', pretty_print=True)

def gerar_xml_s2210(evento, empresa, funcionario, ambiente='2'):
    """Gera XML do evento S-2210 (CAT - Comunicação de Acidente de Trabalho)"""
    ns = "http://www.esocial.gov.br/schema/evt/evtCAT/v02_05_00"
    root = etree.Element("eSocial", xmlns=ns)
    evtCAT = etree.SubElement(root, "evtCAT")

    ideEvento = etree.SubElement(evtCAT, "ideEvento")
    etree.SubElement(ideEvento, "tpAmb").text = ambiente
    etree.SubElement(ideEvento, "procEmi").text = "1"
    etree.SubElement(ideEvento, "verProc").text = "1.0"

    ideEmpregador = etree.SubElement(evtCAT, "ideEmpregador")
    etree.SubElement(ideEmpregador, "tpInsc").text = "1"
    cnpj_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
    etree.SubElement(ideEmpregador, "nrInsc").text = cnpj_limpo

    ideTrab = etree.SubElement(evtCAT, "ideTrab")
    cpf_limpo = funcionario.cpf.replace('.', '').replace('-', '')
    etree.SubElement(ideTrab, "cpfTrab").text = cpf_limpo

    cat = etree.SubElement(evtCAT, "cat")
    if hasattr(evento, 'data_acidente') and evento.data_acidente:
        etree.SubElement(cat, "dtAcid").text = evento.data_acidente.strftime('%Y-%m-%d')
    if hasattr(evento, 'tipo_acidente') and evento.tipo_acidente:
        etree.SubElement(cat, "tpAcid").text = evento.tipo_acidente
    if hasattr(evento, 'local') and evento.local:
        etree.SubElement(cat, "local").text = evento.local
    if hasattr(evento, 'parte_atingida') and evento.parte_atingida:
        etree.SubElement(cat, "parteAtingida").text = evento.parte_atingida
    if hasattr(evento, 'descricao') and evento.descricao:
        etree.SubElement(cat, "descricao").text = evento.descricao

    return etree.tostring(root, encoding='unicode', pretty_print=True)

def gerar_xml_s2240(evento, empresa, funcionario, ambiente='2'):
    """Gera XML do evento S-2240 (Condições Ambientais do Trabalho - Fatores de Risco)"""
    ns = "http://www.esocial.gov.br/schema/evt/evtExpRisco/v02_05_00"
    root = etree.Element("eSocial", xmlns=ns)
    evtExpRisco = etree.SubElement(root, "evtExpRisco")

    ideEvento = etree.SubElement(evtExpRisco, "ideEvento")
    etree.SubElement(ideEvento, "tpAmb").text = ambiente
    etree.SubElement(ideEvento, "procEmi").text = "1"
    etree.SubElement(ideEvento, "verProc").text = "1.0"

    ideEmpregador = etree.SubElement(evtExpRisco, "ideEmpregador")
    etree.SubElement(ideEmpregador, "tpInsc").text = "1"
    cnpj_limpo = empresa.cnpj.replace('.', '').replace('/', '').replace('-', '')
    etree.SubElement(ideEmpregador, "nrInsc").text = cnpj_limpo

    ideTrab = etree.SubElement(evtExpRisco, "ideTrab")
    cpf_limpo = funcionario.cpf.replace('.', '').replace('-', '')
    etree.SubElement(ideTrab, "cpfTrab").text = cpf_limpo

    expRisco = etree.SubElement(evtExpRisco, "expRisco")
    if hasattr(evento, 'data_avaliacao') and evento.data_avaliacao:
        etree.SubElement(expRisco, "dtAval").text = evento.data_avaliacao.strftime('%Y-%m-%d')
    agente = etree.SubElement(expRisco, "agente")
    if hasattr(evento, 'agente_risco') and evento.agente_risco:
        etree.SubElement(agente, "codAgente").text = evento.agente_risco
    if hasattr(evento, 'intensidade') and evento.intensidade:
        etree.SubElement(agente, "intensidade").text = evento.intensidade
    if hasattr(evento, 'epi_utilizado') and evento.epi_utilizado:
        etree.SubElement(agente, "epi").text = evento.epi_utilizado

    return etree.tostring(root, encoding='unicode', pretty_print=True)

def enviar_lote(xml_assinado, ambiente='2'):
    """
    Envia o lote de eventos (um único evento) via SOAP e retorna o recibo.
    xml_assinado: string do XML já assinado.
    """
    url = WS_URL_HOMOLOG if ambiente == '2' else WS_URL_PROD
    soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
    <soap12:Body>
        <EnviarLoteEventos xmlns="http://www.esocial.gov.br/schema/lote/eventos/envio/v1_0_0">
            <loteEventos>
                <evento>
                    {xml_assinado}
                </evento>
            </loteEventos>
        </EnviarLoteEventos>
    </soap12:Body>
</soap12:Envelope>"""
    headers = {
        'Content-Type': 'application/soap+xml; charset=utf-8',
        'SOAPAction': 'http://www.esocial.gov.br/eventos'
    }
    response = requests.post(url, data=soap.encode('utf-8'), headers=headers)
    return response.text