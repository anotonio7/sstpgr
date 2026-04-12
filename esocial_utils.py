import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os


# ================= CONFIGURAÇÃO =================
# O modo real agora é controlado pelo banco de dados
# Não mude mais esta variável manualmente!
# ================================================

def is_modo_producao():
    """Verifica se o modo produção está ativo"""
    try:
        from main import db, ConfigSistema
        config = ConfigSistema.query.filter_by(chave='modo_envio').first()
        if config:
            return config.valor.lower() == 'true'
        return False
    except:
        return False


def carregar_certificado(pfx_path, senha):
    """Carrega certificado A1 no formato .pfx"""
    if not is_modo_producao():
        print("⚠️ MODO TESTE: Certificado ignorado")
        return "cert_teste", "key_teste"

    try:
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

        print(f"📂 Carregando certificado: {pfx_path}")

        with open(pfx_path, 'rb') as f:
            pfx_data = f.read()

        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data,
            senha.encode('utf-8')
        )

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
        raise


def assinar_xml(xml_string, cert_pem, key_pem):
    """Assina o XML com certificado digital"""
    if not is_modo_producao():
        print("⚠️ MODO TESTE: XML não assinado")
        return xml_string

    try:
        from lxml import etree
        from signxml import XMLSigner

        print("🔐 Assinando XML...")
        root = etree.fromstring(xml_string.encode('utf-8'))

        signer = XMLSigner(
            method='dsig',
            signature_algorithm='rsa-sha256',
            digest_algorithm='sha256',
            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        )

        signed_root = signer.sign(root, key=key_pem, cert=cert_pem)

        print("✅ XML assinado com sucesso!")
        return etree.tostring(signed_root, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')

    except Exception as e:
        print(f"❌ Erro ao assinar XML: {e}")
        raise


def enviar_lote(xml_assinado, ambiente='2'):
    """Envia lote para o eSocial (REAL ou TESTE)"""

    if not is_modo_producao():
        # MODO TESTE - Simulado
        print("=" * 60)
        print("⚠️ MODO TESTE - Envio simulado para eSocial")
        print(f"Ambiente: {'Produção' if ambiente == '1' else 'Homologação'}")
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Tamanho do XML: {len(xml_assinado)} bytes")
        print("=" * 60)

        return f"RECIBO_SIMULADO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # MODO REAL - Envio efetivo
    try:
        # URLs do eSocial
        if ambiente == '1':
            url = 'https://webservices.producaorestrita.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos'
            print("📍 Ambiente: PRODUÇÃO")
        else:
            url = 'https://webserviceshom.estaleiro.serpro.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos'
            print("📍 Ambiente: HOMOLOGAÇÃO")

        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': 'http://www.esocial.gov.br/servicos/empregador/enviarloteeventos/WsEnviarLoteEventos'
        }

        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
    <soap12:Header/>
    <soap12:Body>
        <EnviarLoteEventosRequest xmlns="http://www.esocial.gov.br/servicos/empregador/enviarloteeventos/v1_0_0">
            <loteEventos>
                <grupo>
                    <ideEmpregador>
                        <tpInsc>1</tpInsc>
                        <nrInsc>00000000</nrInsc>
                    </ideEmpregador>
                    <eventos>
                        <evento>{xml_assinado}</evento>
                    </eventos>
                </grupo>
            </loteEventos>
        </EnviarLoteEventosRequest>
    </soap12:Body>
</soap12:Envelope>"""

        print(f"📤 Enviando para o eSocial REAL...")
        print(f"URL: {url}")

        response = requests.post(url, data=soap_envelope.encode('utf-8'), headers=headers, timeout=60)

        print(f"Status da resposta: {response.status_code}")

        # Extrai recibo
        import re
        padrao_recibo = r'<recibo>(.*?)</recibo>'
        match = re.search(padrao_recibo, response.text, re.DOTALL)

        if match:
            recibo = match.group(1)
            print(f"✅ Recibo recebido: {recibo[:100]}...")
            return recibo

        return f"Resposta do eSocial: {response.text[:200]}..."

    except Exception as e:
        print(f"❌ Erro ao enviar: {e}")
        raise


# Mantenha suas funções gerar_xml_* aqui...
def gerar_xml_s2220(evento, empresa, funcionario, ambiente='2'):
    # ... seu código existente ...
    pass


def gerar_xml_s2221(evento, empresa, funcionario, ambiente='2'):
    # ... seu código existente ...
    pass


def gerar_xml_s2210(evento, empresa, funcionario, ambiente='2'):
    # ... seu código existente ...
    pass


def gerar_xml_s2240(evento, empresa, funcionario, ambiente='2'):
    # ... seu código existente ...
    pass