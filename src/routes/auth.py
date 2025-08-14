from flask import Blueprint, request, jsonify
from src.models.database import db, User
from src.utils.cpf_validator import validate_cpf_complete
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def validate_cpf(cpf):
    """Validação básica de CPF (formato)"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    return len(cpf) == 11 and cpf.isdigit()

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        cpf = data.get('cpf', '').replace('.', '').replace('-', '')
        data_nascimento = data.get('data_nascimento')
        
        if not cpf or not data_nascimento:
            return jsonify({'error': 'CPF e data de nascimento são obrigatórios'}), 400
        
        # Validação completa do CPF
        cpf_validation = validate_cpf_complete(cpf, data_nascimento)
        if not cpf_validation['valid']:
            return jsonify({'error': cpf_validation['message']}), 400
        
        try:
            data_nascimento_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Data de nascimento inválida'}), 400
        
        # Verificar se o usuário existe
        user = User.query.filter_by(cpf=cpf, data_nascimento=data_nascimento_obj).first()
        
        if user:
            # Usuário existe - verificar se tem agendamentos
            has_appointments = len(user.appointments) > 0
            return jsonify({
                'success': True,
                'user_exists': True,
                'user_id': user.id,
                'has_appointments': has_appointments,
                'user_data': {
                    'cpf': user.cpf,
                    'nome_completo': user.nome_completo,
                    'celular': user.celular,
                    'carteira_sus': user.carteira_sus
                },
                'cpf_validation': cpf_validation
            })
        else:
            # Usuário não existe - criar novo
            new_user = User(
                cpf=cpf,
                data_nascimento=data_nascimento_obj
            )
            db.session.add(new_user)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'user_exists': False,
                'user_id': new_user.id,
                'has_appointments': False,
                'user_data': {
                    'cpf': new_user.cpf,
                    'nome_completo': None,
                    'celular': None,
                    'carteira_sus': None
                },
                'cpf_validation': cpf_validation
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/update-user', methods=['PUT'])
def update_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Atualizar dados do usuário
        if 'nome_completo' in data:
            user.nome_completo = data['nome_completo']
        if 'celular' in data:
            user.celular = data['celular']
        if 'carteira_sus' in data:
            user.carteira_sus = data['carteira_sus']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Dados atualizados com sucesso'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'cpf': user.cpf,
                'nome_completo': user.nome_completo,
                'celular': user.celular,
                'carteira_sus': user.carteira_sus,
                'data_nascimento': user.data_nascimento.isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

