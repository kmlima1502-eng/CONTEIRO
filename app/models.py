from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(20), unique=True, nullable=True)
    senha_hash = db.Column(db.String(255), nullable=True)

    # Relacionamentos
    categorias = db.relationship('Categoria', backref='user', lazy=True)
    transacoes = db.relationship('Transacao', backref='user', lazy=True)
    metas = db.relationship('MetaOrcamentaria', backref='user', lazy=True)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'receita' ou 'despesa'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    subcategorias = db.relationship('Subcategoria', backref='categoria', cascade="all, delete-orphan", lazy=True)
    transacoes = db.relationship('Transacao', backref='categoria_ref', lazy=True)

class Subcategoria(db.Model):
    __tablename__ = 'subcategorias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)

class Transacao(db.Model):
    __tablename__ = 'transacoes'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'receita' ou 'despesa'
    status = db.Column(db.String(10), default='pendente')  # 'pendente' ou 'pago'
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    centro_custo = db.Column(db.String(50), nullable=True) # Tags de projeto
    conciliado = db.Column(db.Boolean, default=False)
    
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    subcategoria_id = db.Column(db.Integer, db.ForeignKey('subcategorias.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class MetaOrcamentaria(db.Model):
    __tablename__ = 'metas_orcamentarias'
    id = db.Column(db.Integer, primary_key=True)
    mes_ano = db.Column(db.String(7), nullable=False)  # Formato 'YYYY-MM'
    teto_gasto = db.Column(db.Float, nullable=False)
    
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)