#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.database import db, City, UBS, Service, Admin, Slot
from src.main import app
import bcrypt
from datetime import date, timedelta

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def populate_database():
    with app.app_context():
        # Limpar dados existentes
        db.drop_all()
        db.create_all()
        
        # Criar cidades
        cidade_sp = City(nome='São Paulo')
        cidade_rj = City(nome='Rio de Janeiro')
        cidade_bh = City(nome='Belo Horizonte')
        
        db.session.add_all([cidade_sp, cidade_rj, cidade_bh])
        db.session.commit()
        
        # Criar UBS
        ubs_sp1 = UBS(nome='UBS Vila Madalena', endereco='Rua Harmonia, 123', cidade_id=cidade_sp.id)
        ubs_sp2 = UBS(nome='UBS Jardins', endereco='Av. Paulista, 456', cidade_id=cidade_sp.id)
        ubs_rj1 = UBS(nome='UBS Copacabana', endereco='Av. Atlântica, 789', cidade_id=cidade_rj.id)
        ubs_bh1 = UBS(nome='UBS Centro', endereco='Rua da Bahia, 321', cidade_id=cidade_bh.id)
        
        db.session.add_all([ubs_sp1, ubs_sp2, ubs_rj1, ubs_bh1])
        db.session.commit()
        
        # Criar serviços
        servico_clinico = Service(nome='Clínico Geral', descricao='Consulta médica geral')
        servico_dentista = Service(nome='Dentista', descricao='Consulta odontológica')
        servico_pediatra = Service(nome='Pediatra', descricao='Consulta pediátrica')
        servico_gineco = Service(nome='Ginecologista', descricao='Consulta ginecológica')
        servico_cardio = Service(nome='Cardiologista', descricao='Consulta cardiológica')
        
        db.session.add_all([servico_clinico, servico_dentista, servico_pediatra, servico_gineco, servico_cardio])
        db.session.commit()
        
        # Associar serviços às UBS
        ubs_sp1.services.extend([servico_clinico, servico_dentista, servico_pediatra])
        ubs_sp2.services.extend([servico_clinico, servico_gineco, servico_cardio])
        ubs_rj1.services.extend([servico_clinico, servico_dentista, servico_gineco])
        ubs_bh1.services.extend([servico_clinico, servico_pediatra, servico_cardio])
        
        db.session.commit()
        
        # Criar administradores
        admin_super = Admin(
            username='admin',
            password_hash=hash_password('admin123'),
            role='SuperAdmin'
        )
        
        admin_ubs1 = Admin(
            username='gestor_sp1',
            password_hash=hash_password('gestor123'),
            role='UBSManager',
            ubs_id=ubs_sp1.id
        )
        
        db.session.add_all([admin_super, admin_ubs1])
        db.session.commit()
        
        # Criar slots (vagas) para os próximos 30 dias
        today = date.today()
        for i in range(30):
            data_slot = today + timedelta(days=i)
            
            # Pular fins de semana
            if data_slot.weekday() >= 5:
                continue
            
            # Criar slots para cada UBS e serviço
            for ubs in [ubs_sp1, ubs_sp2, ubs_rj1, ubs_bh1]:
                for service in ubs.services:
                    # Manhã
                    slot_manha = Slot(
                        ubs_id=ubs.id,
                        service_id=service.id,
                        data=data_slot,
                        turno='Manhã',
                        quantidade_disponivel=5,
                        quantidade_total=5
                    )
                    
                    # Tarde
                    slot_tarde = Slot(
                        ubs_id=ubs.id,
                        service_id=service.id,
                        data=data_slot,
                        turno='Tarde',
                        quantidade_disponivel=5,
                        quantidade_total=5
                    )
                    
                    db.session.add_all([slot_manha, slot_tarde])
        
        db.session.commit()
        
        print("Banco de dados populado com sucesso!")
        print("\nCredenciais de acesso:")
        print("Super Admin: admin / admin123")
        print("Gestor UBS SP1: gestor_sp1 / gestor123")
        print("\nCidades criadas:", [c.nome for c in [cidade_sp, cidade_rj, cidade_bh]])
        print("UBS criadas:", [u.nome for u in [ubs_sp1, ubs_sp2, ubs_rj1, ubs_bh1]])
        print("Serviços criados:", [s.nome for s in [servico_clinico, servico_dentista, servico_pediatra, servico_gineco, servico_cardio]])

if __name__ == '__main__':
    populate_database()

