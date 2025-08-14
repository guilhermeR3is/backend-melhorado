from flask import Blueprint, request, jsonify
from src.models.database import db, User, City, UBS, Service, Appointment, Slot
from datetime import datetime, date
from sqlalchemy import and_

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/cities', methods=['GET'])
def get_cities():
    try:
        cities = City.query.all()
        return jsonify({
            'success': True,
            'cities': [{'id': city.id, 'nome': city.nome} for city in cities]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/ubs/<city_id>', methods=['GET'])
def get_ubs_by_city(city_id):
    try:
        ubs_list = UBS.query.filter_by(cidade_id=city_id).all()
        return jsonify({
            'success': True,
            'ubs': [{'id': ubs.id, 'nome': ubs.nome, 'endereco': ubs.endereco} for ubs in ubs_list]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/services/<ubs_id>', methods=['GET'])
def get_services_by_ubs(ubs_id):
    try:
        ubs = UBS.query.get(ubs_id)
        if not ubs:
            return jsonify({'error': 'UBS não encontrada'}), 404
        
        services = ubs.services
        return jsonify({
            'success': True,
            'services': [{'id': service.id, 'nome': service.nome, 'descricao': service.descricao} for service in services]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/available-dates', methods=['POST'])
def get_available_dates():
    try:
        data = request.get_json()
        ubs_id = data.get('ubs_id')
        service_id = data.get('service_id')
        
        if not ubs_id or not service_id:
            return jsonify({'error': 'UBS e serviço são obrigatórios'}), 400
        
        # Buscar slots disponíveis (com quantidade_disponivel > 0)
        today = date.today()
        slots = Slot.query.filter(
            and_(
                Slot.ubs_id == ubs_id,
                Slot.service_id == service_id,
                Slot.data >= today,
                Slot.quantidade_disponivel > 0
            )
        ).all()
        
        # Agrupar por data
        dates_dict = {}
        for slot in slots:
            date_str = slot.data.isoformat()
            if date_str not in dates_dict:
                dates_dict[date_str] = {'data': date_str, 'turnos': {}}
            
            dates_dict[date_str]['turnos'][slot.turno] = {
                'disponivel': slot.quantidade_disponivel,
                'total': slot.quantidade_total
            }
        
        available_dates = list(dates_dict.values())
        
        return jsonify({
            'success': True,
            'available_dates': available_dates
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/create', methods=['POST'])
def create_appointment():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        ubs_id = data.get('ubs_id')
        service_id = data.get('service_id')
        data_agendamento = data.get('data_agendamento')
        turno = data.get('turno')
        
        if not all([user_id, ubs_id, service_id, data_agendamento, turno]):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
        
        try:
            data_agendamento_obj = datetime.strptime(data_agendamento, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Data de agendamento inválida'}), 400
        
        # Verificar se existe slot disponível
        slot = Slot.query.filter(
            and_(
                Slot.ubs_id == ubs_id,
                Slot.service_id == service_id,
                Slot.data == data_agendamento_obj,
                Slot.turno == turno,
                Slot.quantidade_disponivel > 0
            )
        ).first()
        
        if not slot:
            return jsonify({'error': 'Não há vagas disponíveis para esta data e turno'}), 400
        
        # Verificar se o usuário já tem agendamento para a mesma data
        existing_appointment = Appointment.query.filter(
            and_(
                Appointment.user_id == user_id,
                Appointment.data_agendamento == data_agendamento_obj,
                Appointment.status == 'Confirmado'
            )
        ).first()
        
        if existing_appointment:
            return jsonify({'error': 'Você já tem um agendamento para esta data'}), 400
        
        # Criar o agendamento
        appointment = Appointment(
            user_id=user_id,
            ubs_id=ubs_id,
            service_id=service_id,
            data_agendamento=data_agendamento_obj,
            turno=turno
        )
        
        # Reduzir a quantidade disponível no slot
        slot.quantidade_disponivel -= 1
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'appointment_id': appointment.id,
            'message': 'Agendamento criado com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/user/<user_id>', methods=['GET'])
def get_user_appointments(user_id):
    try:
        appointments = Appointment.query.filter_by(user_id=user_id).all()
        
        appointments_data = []
        for appointment in appointments:
            appointments_data.append({
                'id': appointment.id,
                'data_agendamento': appointment.data_agendamento.isoformat(),
                'turno': appointment.turno,
                'status': appointment.status,
                'ubs_nome': appointment.ubs.nome,
                'service_nome': appointment.service.nome,
                'cidade_nome': appointment.ubs.city.nome,
                'created_at': appointment.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'appointments': appointments_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointments_bp.route('/cancel/<appointment_id>', methods=['PUT'])
def cancel_appointment(appointment_id):
    try:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        
        if appointment.status != 'Confirmado':
            return jsonify({'error': 'Agendamento não pode ser cancelado'}), 400
        
        # Cancelar o agendamento
        appointment.status = 'Cancelado'
        
        # Aumentar a quantidade disponível no slot
        slot = Slot.query.filter(
            and_(
                Slot.ubs_id == appointment.ubs_id,
                Slot.service_id == appointment.service_id,
                Slot.data == appointment.data_agendamento,
                Slot.turno == appointment.turno
            )
        ).first()
        
        if slot:
            slot.quantidade_disponivel += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Agendamento cancelado com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

