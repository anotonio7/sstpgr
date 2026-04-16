from main import app, db
from models import EventoS2240, ConfigCertificado, ReciboEnvio
from functions_s2240 import gerar_xml_s2240
from esocial_utils import enviar_lote, carregar_certificado, assinar_xml
from datetime import datetime

print("Iniciando script...")

with app.app_context():
    print("Buscando evento pendente...")
    evento = EventoS2240.query.filter_by(status="pendente").first()
    
    if not evento:
        print("Nenhum evento pendente encontrado!")
    else:
        print(f"Evento encontrado: ID {evento.id}")
        
        print("Buscando certificado...")
        cfg = ConfigCertificado.query.first()
        
        if not cfg:
            print("Certificado não configurado!")
        else:
            print("Certificado OK")
            
            print("Gerando XML...")
            xml_gerado = gerar_xml_s2240(evento, evento.funcionario.empresa, evento.funcionario)
            
            if not xml_gerado:
                print("Erro: XML vazio!")
            else:
                print(f"XML gerado: {len(xml_gerado)} bytes")
                
                print("Carregando certificado...")
                cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
                
                print("Assinando XML...")
                xml_assinado = assinar_xml(xml_gerado, cert_pem, key_pem)
                
                print("Enviando para eSocial...")
                resposta = enviar_lote(xml_assinado, str(cfg.ambiente))
                
                print(f"Resposta recebida: {resposta}")
                
                print("Salvando recibo...")
                nome_xml = f"S2240_{evento.funcionario.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                
                recibo = ReciboEnvio(
                    evento_tipo="S-2240",
                    evento_id=evento.id,
                    protocolo=str(resposta)[:100],
                    status="enviado",
                    resposta_completa=str(resposta),
                    data_envio=datetime.now(),
                    funcionario_id=evento.funcionario_id,
                    nome_xml=nome_xml
                )
                db.session.add(recibo)
                evento.status = "enviado"
                evento.data_envio = datetime.now()
                db.session.commit()
                
                print(f"✅ Recibo salvo com sucesso! ID: {recibo.id}")
                print(f"✅ Evento ID {evento.id} marcado como enviado")

print("Script finalizado!")
