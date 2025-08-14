import re
import requests

def validate_cpf_format(cpf):
    """Validação básica de formato do CPF"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verificar se não são todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False
    
    return True

def calculate_cpf_digit(cpf_digits, weights):
    """Calcula um dígito verificador do CPF"""
    total = sum(int(digit) * weight for digit, weight in zip(cpf_digits, weights))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder

def validate_cpf_algorithm(cpf):
    """Validação completa do algoritmo do CPF"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if not validate_cpf_format(cpf):
        return False
    
    # Calcular primeiro dígito verificador
    first_weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    first_digit = calculate_cpf_digit(cpf[:9], first_weights)
    
    # Calcular segundo dígito verificador
    second_weights = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    second_digit = calculate_cpf_digit(cpf[:10], second_weights)
    
    # Verificar se os dígitos calculados coincidem com os informados
    return cpf[9:11] == f"{first_digit}{second_digit}"

def validate_cpf_with_receita_federal(cpf, data_nascimento):
    """
    Tentativa de validação com a Receita Federal
    Nota: Este é um exemplo conceitual. A Receita Federal não oferece
    uma API pública gratuita para validação de CPF.
    """
    try:
        # Este é apenas um exemplo de como seria a estrutura
        # Na prática, seria necessário usar um serviço pago ou
        # implementar uma solução alternativa
        
        # Simulação de resposta para desenvolvimento
        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        
        # Validação básica do algoritmo
        if not validate_cpf_algorithm(cpf_clean):
            return {
                'valid': False,
                'message': 'CPF inválido pelo algoritmo de verificação'
            }
        
        # Simulação de validação com dados da Receita Federal
        # Em um ambiente real, aqui seria feita a consulta à API oficial
        return {
            'valid': True,
            'message': 'CPF válido',
            'source': 'algorithm_validation'  # Indicando que foi validado apenas pelo algoritmo
        }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'Erro na validação: {str(e)}'
        }

def validate_cpf_complete(cpf, data_nascimento=None):
    """
    Validação completa do CPF
    1. Validação de formato
    2. Validação do algoritmo
    3. Tentativa de validação com fonte oficial (se disponível)
    """
    cpf_clean = re.sub(r'[^0-9]', '', cpf)
    
    # Validação de formato
    if not validate_cpf_format(cpf_clean):
        return {
            'valid': False,
            'message': 'CPF com formato inválido'
        }
    
    # Validação do algoritmo
    if not validate_cpf_algorithm(cpf_clean):
        return {
            'valid': False,
            'message': 'CPF inválido pelo algoritmo de verificação'
        }
    
    # Tentativa de validação com fonte oficial
    if data_nascimento:
        return validate_cpf_with_receita_federal(cpf_clean, data_nascimento)
    
    return {
        'valid': True,
        'message': 'CPF válido pelo algoritmo de verificação',
        'source': 'algorithm_only'
    }

