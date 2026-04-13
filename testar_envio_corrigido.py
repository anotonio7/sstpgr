from main import app, db
from models import EventoS2240, ConfigCertificado, ReciboEnvio
from functions_s2240 import gerar_xml_s2240
from esocial_utils import enviar_lote, carregar_certificado, assinar_xml
from datetime import datetime

with app.app_context():
    print("="*50)
    print("TESTE DE ENVIO S-2240")
    print("="*50)
    
    # Pega um evento pendente
    evento = EventoS2240.query.filter_by(status='pendente').first()
    
    if not evento:
        print("❌ Nenhum evento pendente encontrado")
        exit()
    
    print(f"✅ Evento encontrado: ID {evento.id}")
    
    # Verifica certificado
    cfg = ConfigCertificado.query.first()
    if not cfg:
        print("❌ Certificado não configurado")
        exit()
    
    print(f"✅ Certificado encontrado (Ambiente: {cfg.ambiente})")
    
    # Gera XML
    xml_gerado = gerar_xml_s2240(
        evento,
        evento.funcionario.empresa,
        evento.funcionario
    )
    
    if not xml_gerado:
        print("❌ Falha ao gerar XML")
        exit()
    
    print(f"✅ XML gerado: {len(xml_gerado)} bytes")
    
    # Carrega certificado
    cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
    
    # Assina XML
    xml_assinado = assinar_xml(xml_gerado, cert_pem, key_pem)
    
    # Envia
    resposta = enviar_lote(xml_assinado, str(cfg.ambiente))
    
    print(f"✅ Enviado! Resposta: {resposta}")
    print(f"Tipo da resposta: {type(resposta)}")
    
    # CORREÇÃO: Verifica se resposta é dicionário ou string
    if isinstance(resposta, dict):
        protocolo = resposta.get('protocolo', '')
        status_resposta = resposta.get('status', 'enviado')
        resposta_completa = str(resposta)
    else:
        # Se for string, usa como está
        protocolo = resposta[:50] if len(resposta) > 50 else resposta
        status_resposta = 'enviado'
        resposta_completa = resposta
    
    # SALVA RECIBO
    nome_xml = f"S2240_{evento.funcionario.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
    
    recibo = ReciboEnvio(
        evento_tipo='S-2240',
        evento_id=evento.id,
        protocolo=protocolo,
        status=status_resposta,
        resposta_completa=resposta_completa,
        data_envio=datetime.now(),
        funcionario_id=evento.funcionario_id,
        nome_xml=nome_xml
    )
    db.session.add(recibo)
    
    # Atualiza evento
    evento.status = 'enviado'
    evento.data_envio = datetime.now()
    
    db.session.commit()
    
    print(f"✅ Recibo salvo! ID: {recibo.id}")
    print("="*50)
