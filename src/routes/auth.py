from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.models.auth import User, db
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valida força da senha"""
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    return True, "Senha válida"

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Registrar novo usuário"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        full_name = data['full_name'].strip()
        company_name = data.get('company_name', '').strip()
        phone = data.get('phone', '').strip()
        
        # Validações
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': 'Nome de usuário deve ter pelo menos 3 caracteres'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Email inválido'
            }), 400
        
        is_valid, password_msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': password_msg
            }), 400
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'error': 'Nome de usuário já existe'
            }), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'error': 'Email já está cadastrado'
            }), 400
        
        # Criar novo usuário
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            company_name=company_name,
            phone=phone
        )
        user.set_password(password)
        
        # Primeiro usuário é admin
        if User.query.count() == 0:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Fazer login do usuário"""
    try:
        data = request.get_json()
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username_or_email or not password:
            return jsonify({
                'success': False,
                'error': 'Username/email e senha são obrigatórios'
            }), 400
        
        # Buscar usuário por username ou email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email.lower())
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'error': 'Credenciais inválidas'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Conta desativada'
            }), 401
        
        # Fazer login
        login_user(user, remember=remember)
        
        # Atualizar último login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Fazer logout do usuário"""
    try:
        logout_user()
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auth/profile', methods=['GET'])
@login_required
def get_profile():
    """Obter perfil do usuário atual"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auth/profile', methods=['PUT'])
@login_required
def update_profile():
    """Atualizar perfil do usuário"""
    try:
        data = request.get_json()
        
        # Campos que podem ser atualizados
        updatable_fields = ['full_name', 'company_name', 'phone']
        
        for field in updatable_fields:
            if field in data:
                setattr(current_user, field, data[field].strip() if data[field] else None)
        
        # Atualizar email (com validação)
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if not validate_email(new_email):
                return jsonify({
                    'success': False,
                    'error': 'Email inválido'
                }), 400
            
            # Verificar se email já existe (exceto o atual)
            existing_user = User.query.filter(
                User.email == new_email,
                User.id != current_user.id
            ).first()
            
            if existing_user:
                return jsonify({
                    'success': False,
                    'error': 'Email já está em uso'
                }), 400
            
            current_user.email = new_email
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Perfil atualizado com sucesso',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auth/change-password', methods=['POST'])
@login_required
def change_password():
    """Alterar senha do usuário"""
    try:
        data = request.get_json()
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({
                'success': False,
                'error': 'Todos os campos são obrigatórios'
            }), 400
        
        # Verificar senha atual
        if not current_user.check_password(current_password):
            return jsonify({
                'success': False,
                'error': 'Senha atual incorreta'
            }), 400
        
        # Verificar se as novas senhas coincidem
        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'error': 'Nova senha e confirmação não coincidem'
            }), 400
        
        # Validar nova senha
        is_valid, password_msg = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': password_msg
            }), 400
        
        # Atualizar senha
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/auth/users', methods=['GET'])
@login_required
def list_users():
    """Listar usuários (apenas para admins)"""
    try:
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Acesso negado'
            }), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        query = User.query
        
        if search:
            query = query.filter(
                (User.username.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%')) |
                (User.full_name.ilike(f'%{search}%'))
            )
        
        users = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

