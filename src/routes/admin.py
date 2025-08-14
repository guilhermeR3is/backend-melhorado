from flask import Blueprint, request, jsonify
from src.models.database import db, Admin, City, UBS, Service, Slot, Appointment, ubs_services
import bcrypt
from datetime import datetime, date

admin_bp = Blueprint('admin', __name__)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username e senha são obrigatórios'}), 400
        
        admin = Admin.query.filter_by(username=username).first()
        
        if not admin or not check_password(password, admin.password_hash):
            return jsonify({'error': 'Credenciais inválidas'}), 401
        
        return jsonify({
            'success': True,
            'admin_id': admin.id,
            'role': admin.role,
            'ubs_id': admin.ubs_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/cities', methods=['GET', 'POST'])
def manage_cities():
    if request.method == 'GET':
        try:
            cities = City.query.all()
            return jsonify({
                'success': True,
                'cities': [{'id': city.id, 'nome': city.nome} for city in cities]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            nome = data.get('nome')
            
            if not nome:
                return jsonify({'error': 'Nome da cidade é obrigatório'}), 400
            
            # Verificar se a cidade já existe
            existing_city = City.query.filter_by(nome=nome).first()
            if existing_city:
                return jsonify({'error': 'Cidade já existe'}), 400
            
            city = City(nome=nome)
            db.session.add(city)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'city_id': city.id,
                'message': 'Cidade criada com sucesso'
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_bp.route('/ubs', methods=['GET', 'POST'])
def manage_ubs():
    if request.method == 'GET':
        try:
            city_id = request.args.get('city_id')
            if city_id:
                ubs_list = UBS.query.filter_by(cidade_id=city_id).all()
            else:
                ubs_list = UBS.query.all()
            
            ubs_data = []
            for ubs in ubs_list:
                ubs_data.append({
                    'id': ubs.id,
                    'nome': ubs.nome,
                    'endereco': ubs.endereco,
                    'cidade_id': ubs.cidade_id,
                    'cidade_nome': ubs.city.nome
                })
            
            return jsonify({
                'success': True,
                'ubs': ubs_data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            nome = data.get('nome')
            endereco = data.get('endereco')
            cidade_id = data.get('cidade_id')
            
            if not nome or not cidade_id:
                return jsonify({'error': 'Nome e cidade são obrigatórios'}), 400
            
            ubs = UBS(nome=nome, endereco=endereco, cidade_id=cidade_id)
            db.session.add(ubs)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'ubs_id': ubs.id,
                'message': 'UBS criada com sucesso'
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_bp.route('/services', methods=['GET', 'POST'])
def manage_services():
    if request.method == 'GET':
        try:
            services = Service.query.all()
            return jsonify({
                'success': True,
                'services': [{'id': service.id, 'nome': service.nome, 'descricao': service.descricao} for service in services]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            nome = data.get('nome')
            descricao = data.get('descricao', '')
            
            if not nome:
                return jsonify({'error': 'Nome do serviço é obrigatório'}), 400
            
            service = Service(nome=nome, descricao=descricao)
            db.session.add(service)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'service_id': service.id,
                'message': 'Serviço criado com sucesso'
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_bp.route('/ubs-services', methods=['POST'])
def assign_service_to_ubs():
    try:
        data = request.get_json()
        ubs_id = data.get('ubs_id')
        service_id = data.get('service_id')
        
        if not ubs_id or not service_id:
            return jsonify({'error': 'UBS e serviço são obrigatórios'}), 400
        
        ubs = UBS.query.get(ubs_id)
        service = Service.query.get(service_id)
        
        if not ubs or not service:
            return jsonify({'error': 'UBS ou serviço não encontrado'}), 404
        
        # Verificar se a associação já existe
        if service in ubs.services:
            return jsonify({'error': 'Serviço já está associado a esta UBS'}), 400
        
        ubs.services.append(service)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Serviço associado à UBS com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/slots', methods=['GET', 'POST'])
def manage_slots():
    if request.method == 'GET':
        try:
            ubs_id = request.args.get('ubs_id')
            service_id = request.args.get('service_id')
            data_inicio = request.args.get('data_inicio')
            data_fim = request.args.get('data_fim')
            
            query = Slot.query
            
            if ubs_id:
                query = query.filter_by(ubs_id=ubs_id)
            if service_id:
                query = query.filter_by(service_id=service_id)
            if data_inicio:
                query = query.filter(Slot.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
            if data_fim:
                query = query.filter(Slot.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
            
            slots = query.all()
            
            slots_data = []
            for slot in slots:
                slots_data.append({
                    'id': slot.id,
                    'ubs_id': slot.ubs_id,
                    'ubs_nome': slot.ubs.nome,
                    'service_id': slot.service_id,
                    'service_nome': slot.service.nome,
                    'data': slot.data.isoformat(),
                    'turno': slot.turno,
                    'quantidade_disponivel': slot.quantidade_disponivel,
                    'quantidade_total': slot.quantidade_total
                })
            
            return jsonify({
                'success': True,
                'slots': slots_data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            ubs_id = data.get('ubs_id')
            service_id = data.get('service_id')
            data_slot = data.get('data')
            turno = data.get('turno')
            quantidade_total = data.get('quantidade_total')
            
            if not all([ubs_id, service_id, data_slot, turno, quantidade_total]):
                return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
            
            try:
                data_obj = datetime.strptime(data_slot, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Data inválida'}), 400
            
            # Verificar se o slot já existe
            existing_slot = Slot.query.filter_by(
                ubs_id=ubs_id,
                service_id=service_id,
                data=data_obj,
                turno=turno
            ).first()
            
            if existing_slot:
                return jsonify({'error': 'Slot já existe para esta data e turno'}), 400
            
            slot = Slot(
                ubs_id=ubs_id,
                service_id=service_id,
                data=data_obj,
                turno=turno,
                quantidade_disponivel=quantidade_total,
                quantidade_total=quantidade_total
            )
            
            db.session.add(slot)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'slot_id': slot.id,
                'message': 'Slot criado com sucesso'
            })
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_bp.route('/appointments', methods=['GET'])
def get_appointments():
    try:
        ubs_id = request.args.get('ubs_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = Appointment.query
        
        if ubs_id:
            query = query.filter_by(ubs_id=ubs_id)
        if data_inicio:
            query = query.filter(Appointment.data_agendamento >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
        if data_fim:
            query = query.filter(Appointment.data_agendamento <= datetime.strptime(data_fim, '%Y-%m-%d').date())
        
        appointments = query.all()
        
        appointments_data = []
        for appointment in appointments:
            appointments_data.append({
                'id': appointment.id,
                'user_nome': appointment.user.nome_completo,
                'user_cpf': appointment.user.cpf,
                'user_celular': appointment.user.celular,
                'ubs_nome': appointment.ubs.nome,
                'service_nome': appointment.service.nome,
                'data_agendamento': appointment.data_agendamento.isoformat(),
                'turno': appointment.turno,
                'status': appointment.status,
                'created_at': appointment.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'appointments': appointments_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/create-admin', methods=['POST'])
def create_admin():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'UBSManager')
        ubs_id = data.get('ubs_id')
        
        if not username or not password:
            return jsonify({'error': 'Username e senha são obrigatórios'}), 400
        
        # Verificar se o username já existe
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            return jsonify({'error': 'Username já existe'}), 400
        
        password_hash = hash_password(password)
        
        admin = Admin(
            username=username,
            password_hash=password_hash,
            role=role,
            ubs_id=ubs_id
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'admin_id': admin.id,
            'message': 'Administrador criado com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

