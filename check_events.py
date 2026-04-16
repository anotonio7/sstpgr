from main import app, db
from models import EventoS2220, EventoS2221, EventoS2210, EventoS2240

with app.app_context():
    print("=== EVENTOS NO BANCO ===")
    print(f"S-2220 (ASO): {EventoS2220.query.count()}")
    print(f"S-2221 (Toxicológico): {EventoS2221.query.count()}")
    print(f"S-2210 (CAT): {EventoS2210.query.count()}")
    print(f"S-2240 (Riscos): {EventoS2240.query.count()}")
    
    print("\n=== DETALHES S-2240 ===")
    for e in EventoS2240.query.all():
        print(f"ID: {e.id} - Status: {getattr(e, 'status', 'sem_status')} - Func: {e.funcionario_id}")
