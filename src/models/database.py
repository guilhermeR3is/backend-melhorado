from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    nome_completo = db.Column(db.String(255), nullable=True)
    celular = db.Column(db.String(15), nullable=True)
    carteira_sus = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    appointments = db.relationship('Appointment', backref='user', lazy=True)

class City(db.Model):
    __tablename__ = 'cities'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    
    # Relacionamentos
    ubs_list = db.relationship('UBS', backref='city', lazy=True)

class UBS(db.Model):
    __tablename__ = 'ubs'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    nome = db.Column(db.String(255), nullable=False)
    endereco = db.Column(db.String(500), nullable=True)
    cidade_id = db.Column(db.String(36), db.ForeignKey('cities.id'), nullable=False)
    
    # Relacionamentos
    appointments = db.relationship('Appointment', backref='ubs', lazy=True)
    slots = db.relationship('Slot', backref='ubs', lazy=True)
    services = db.relationship('Service', secondary='ubs_services', backref='ubs_list')

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    appointments = db.relationship('Appointment', backref='service', lazy=True)
    slots = db.relationship('Slot', backref='service', lazy=True)

# Tabela de associação para UBS e Serviços
ubs_services = db.Table('ubs_services',
    db.Column('ubs_id', db.String(36), db.ForeignKey('ubs.id'), primary_key=True),
    db.Column('service_id', db.String(36), db.ForeignKey('services.id'), primary_key=True)
)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    ubs_id = db.Column(db.String(36), db.ForeignKey('ubs.id'), nullable=False)
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'), nullable=False)
    data_agendamento = db.Column(db.Date, nullable=False)
    turno = db.Column(db.String(10), nullable=False)  # 'Manhã' ou 'Tarde'
    status = db.Column(db.String(20), default='Confirmado')  # 'Confirmado', 'Cancelado', 'Realizado'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Slot(db.Model):
    __tablename__ = 'slots'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    ubs_id = db.Column(db.String(36), db.ForeignKey('ubs.id'), nullable=False)
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    turno = db.Column(db.String(10), nullable=False)  # 'Manhã' ou 'Tarde'
    quantidade_disponivel = db.Column(db.Integer, nullable=False)
    quantidade_total = db.Column(db.Integer, nullable=False)

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'SuperAdmin' ou 'UBSManager'
    ubs_id = db.Column(db.String(36), db.ForeignKey('ubs.id'), nullable=True)  # Para gerentes de UBS
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

