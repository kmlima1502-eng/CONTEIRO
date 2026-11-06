from flask import Blueprint, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Categoria

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    nome = data.get('nome')
    email = data.get('email')
    telefone = data.get('telefone')
    senha = data.get('senha')

    if not email or not senha:
        return jsonify({'success': False, 'message': 'Preencha todos os campos obrigatórios!'}), 400

    if User.query.filter((User.email == email) | (User.telefone == telefone)).first():
        return jsonify({'success': False, 'message': 'E-mail ou telefone já cadastrado!'}), 400

    senha_hash = generate_password_hash(senha)
    novo_usuario = User(nome=nome, email=email, telefone=telefone, senha_hash=senha_hash)
    
    db.session.add(novo_usuario)
    db.session.commit()

    # Cria a nova lista exata de categorias ao cadastrar qualquer novo usuário
    cats_padrao = [
        # Contas a Pagar (Despesas)
        Categoria(nome='Carro', tipo='despesa', user_id=novo_usuario.id),
        Categoria(nome='IPTU', tipo='despesa', user_id=novo_usuario.id),
        Categoria(nome='Conta de Energia', tipo='despesa', user_id=novo_usuario.id),
        Categoria(nome='Conta de Água', tipo='despesa', user_id=novo_usuario.id),
        Categoria(nome='Supermercado', tipo='despesa', user_id=novo_usuario.id),
        Categoria(nome='Cartão de crédito', tipo='despesa', user_id=novo_usuario.id),
        Categoria(nome='Gasto pessoal', tipo='despesa', user_id=novo_usuario.id),
        Categoria(nome='Outros', tipo='despesa', user_id=novo_usuario.id),

        # Contas a Receber (Receitas)
        Categoria(nome='Salário', tipo='receita', user_id=novo_usuario.id),
        Categoria(nome='Aluguel', tipo='receita', user_id=novo_usuario.id),
        Categoria(nome='Décimo terceiro', tipo='receita', user_id=novo_usuario.id),
        Categoria(nome='Vendas', tipo='receita', user_id=novo_usuario.id),
        Categoria(nome='Outros', tipo='receita', user_id=novo_usuario.id)
    ]
    db.session.add_all(cats_padrao)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Cadastro realizado com sucesso!'})

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    login_input = data.get('login')
    senha = data.get('senha')
    remember = data.get('remember', False)

    usuario = User.query.filter((User.email == login_input) | (User.telefone == login_input)).first()

    if not usuario or not check_password_hash(usuario.senha_hash, senha):
        return jsonify({'success': False, 'message': 'E-mail, telefone ou senha incorretos!'}), 401

    login_user(usuario, remember=remember)
    return jsonify({'success': True, 'nome': usuario.nome})

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})