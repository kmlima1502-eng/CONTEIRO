from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Transacao, Categoria
from datetime import datetime, date
from sqlalchemy import func

finance_bp = Blueprint('finance', __name__)

LISTA_CATEGORIAS_EXATAS = [
    # 8 Categorias de Contas a Pagar (Despesas)
    {'nome': 'Carro', 'tipo': 'despesa'},
    {'nome': 'IPTU', 'tipo': 'despesa'},
    {'nome': 'Conta de Energia', 'tipo': 'despesa'},
    {'nome': 'Conta de Água', 'tipo': 'despesa'},
    {'nome': 'Supermercado', 'tipo': 'despesa'},
    {'nome': 'Cartão de crédito', 'tipo': 'despesa'},
    {'nome': 'Gasto pessoal', 'tipo': 'despesa'},
    {'nome': 'Outros', 'tipo': 'despesa'},

    # 5 Categorias de Contas a Receber (Receitas)
    {'nome': 'Salário', 'tipo': 'receita'},
    {'nome': 'Aluguel', 'tipo': 'receita'},
    {'nome': 'Décimo terceiro', 'tipo': 'receita'},
    {'nome': 'Vendas', 'tipo': 'receita'},
    {'nome': 'Outros', 'tipo': 'receita'}
]

@finance_bp.route('/')
def index():
    return render_template('index.html')

# ==========================================
# GESTÃO DE TRANSAÇÕES
# ==========================================

@finance_bp.route('/api/transacoes', methods=['GET', 'POST'])
@login_required
def gerenciar_transacoes():
    if request.method == 'POST':
        data = request.get_json()
        nova = Transacao(
            descricao=data['descricao'],
            valor=float(data['valor']),
            tipo=data['tipo'],
            status=data.get('status', 'pendente'),
            data_vencimento=datetime.strptime(data['data_vencimento'], '%Y-%m-%d').date(),
            categoria_id=int(data['categoria_id']),
            user_id=current_user.id,
            deletado=False
        )
        db.session.add(nova)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lançamento efetuado com sucesso!'}), 201

    try:
        transacoes = Transacao.query.filter_by(user_id=current_user.id, deletado=False).order_by(Transacao.data_vencimento.asc()).all()
    except Exception:
        transacoes = Transacao.query.filter_by(user_id=current_user.id).order_by(Transacao.data_vencimento.asc()).all()
    
    saldo_geral = sum(t.valor if t.tipo == 'receita' and t.status == 'pago' else -t.valor for t in transacoes if t.status == 'pago')
    a_receber = sum(t.valor for t in transacoes if t.tipo == 'receita' and t.status == 'pendente')
    a_pagar = sum(t.valor for t in transacoes if t.tipo == 'despesa' and t.status == 'pendente')

    lista = [{
        'id': t.id,
        'descricao': t.descricao,
        'valor': t.valor,
        'tipo': t.tipo,
        'status': t.status,
        'vencimento': t.data_vencimento.strftime('%d/%m/%Y'),
        'categoria': t.categoria_ref.nome if t.categoria_ref else 'Sem Categoria'
    } for t in transacoes]

    return jsonify({
        'transacoes': lista,
        'kpis': {
            'saldo_geral': saldo_geral,
            'a_receber': a_receber,
            'a_pagar': a_pagar
        }
    })

@finance_bp.route('/api/transacoes/<int:id>/status', methods=['PATCH'])
@login_required
def alterar_status(id):
    t = Transacao.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    t.status = data.get('status', 'pago')
    if t.status == 'pago':
        t.data_pagamento = date.today()
    db.session.commit()
    return jsonify({'success': True})

@finance_bp.route('/api/transacoes/<int:id>', methods=['DELETE'])
@login_required
def deletar_transacao(id):
    t = Transacao.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    t.deletado = True
    t.data_deletado = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Lançamento movido para o histórico de exclusões.'})

@finance_bp.route('/api/historico-exclusoes', methods=['GET'])
@login_required
def historico_exclusoes():
    try:
        excluidos = Transacao.query.filter_by(user_id=current_user.id, deletado=True).order_by(Transacao.data_deletado.desc()).all()
    except Exception:
        excluidos = []

    lista = [{
        'id': t.id,
        'descricao': t.descricao,
        'valor': t.valor,
        'tipo': t.tipo,
        'categoria': t.categoria_ref.nome if t.categoria_ref else 'Sem Categoria',
        'data_exclusao': t.data_deletado.strftime('%d/%m/%Y %H:%M') if getattr(t, 'data_deletado', None) else 'N/I'
    } for t in excluidos]
    return jsonify(lista)

# ==========================================
# GESTÃO DE CATEGORIAS
# ==========================================

@finance_bp.route('/api/categorias', methods=['GET'])
@login_required
def gerenciar_categorias():
    categorias = Categoria.query.filter_by(user_id=current_user.id).all()
    nomes_atuais = [c.nome for c in categorias]
    nomes_esperados = [item['nome'] for item in LISTA_CATEGORIAS_EXATAS]
    
    if len(categorias) != 13 or set(nomes_atuais) != set(nomes_esperados):
        Categoria.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        novas_cats = [
            Categoria(nome=item['nome'], tipo=item['tipo'], user_id=current_user.id) 
            for item in LISTA_CATEGORIAS_EXATAS
        ]
        db.session.add_all(novas_cats)
        db.session.commit()
        categorias = Categoria.query.filter_by(user_id=current_user.id).all()

    res = [{'id': c.id, 'nome': c.nome, 'tipo': c.tipo} for c in categorias]
    return jsonify(res)

@finance_bp.route('/api/dashboard/analytics', methods=['GET'])
@login_required
def dashboard_analytics():
    try:
        dados_mensais = db.session.query(
            func.strftime('%Y-%m', Transacao.data_vencimento).label('mes'),
            Transacao.tipo,
            func.sum(Transacao.valor).label('total')
        ).filter(Transacao.user_id == current_user.id, Transacao.deletado == False)\
         .group_by('mes', Transacao.tipo)\
         .order_by('mes').all()
    except Exception:
        dados_mensais = []

    meses = sorted(list(set([d.mes for d in dados_mensais])))
    receitas = [next((d.total for d in dados_mensais if d.mes == m and d.tipo == 'receita'), 0.0) for m in meses]
    despesas = [next((d.total for d in dados_mensais if d.mes == m and d.tipo == 'despesa'), 0.0) for m in meses]

    try:
        distribuicao = db.session.query(
            Categoria.nome,
            func.sum(Transacao.valor).label('total')
        ).join(Transacao, Transacao.categoria_id == Categoria.id)\
         .filter(Transacao.user_id == current_user.id, Transacao.tipo == 'despesa', Transacao.deletado == False)\
         .group_by(Categoria.nome).all()
    except Exception:
        distribuicao = []

    return jsonify({
        'tendencia': {'labels': meses, 'receitas': receitas, 'despesas': despesas},
        'distribuicao': {'labels': [c.nome for c in distribuicao], 'data': [c.total for c in distribuicao]}
    })