from main import app, db
from models import EventoS2240, ConfigCertificado, ReciboEnvio
from functions_s2240 import gerar_xml_s2240
from esocial_utils import enviar_lote, carregar_certificado, assinar_xml
from datetime import datetime

with app.app_context():
    evento = EventoS2240.query.filter_by(status="pendente").first()
    if not evento:
        print("Nenhum evento pendente")
    else:
        print(f"Enviando evento {evento.id}...")
        cfg = ConfigCertificado.query.first()
        if not cfg:
            print("Sem certificado")
        else:
            xml = gerar_xml_s2240(evento, evento.funcionario.empresa, evento.funcionario)
            if xml:
                cert_pem, key_pem = carregar_certificado(cfg.certificado_pfx, cfg.senha)
                xml_ass = assinar_xml(xml, cert_pem, key_pem)
                resposta = enviar_lote(xml_ass, str(cfg.ambiente))
                print(f"Resposta: {resposta}")
                
                nome_xml = f"S2240_{evento.funcionario.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                
                # Usando os campos corretos
                recibo = ReciboEnvio(
                    evento_tipo="S-2240",
                    evento_id=evento.id,
                    nome_xml=nome_xml,
                    recibo=str(resposta),  # protocolo vai no campo 'recibo'
                    data_envio=datetime.now(),
                    status="enviado",
                    mensagem_erro=""
                )
                db.session.add(recibo)
                evento.status = "enviado"
                evento.data_envio = datetime.now()
                db.session.commit()
                print(f"✅ Recibo salvo! ID: {recibo.id}")
            else:
                print("Erro ao gerar XML")
