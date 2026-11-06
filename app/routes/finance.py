from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import db, Transacao, Categoria, Subcategoria, MetaOrcamentaria
from datetime import datetime, date
from sqlalchemy import func

finance_bp = Blueprint('finance', __name__)

@finance_bp.route('/')
def index():
    return render_template('index.html')

# 1. FLUXO DE CAIXA E TRANSAÇÕES
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
            subcategoria_id=int(data['subcategoria_id']) if data.get('subcategoria_id') else None,
            centro_custo=data.get('centro_custo'),
            user_id=current_user.id
        )
        db.session.add(nova)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lançamento efetuado com sucesso!'}), 201

    # Busca transações do usuário logado
    transacoes = Transacao.query.filter_by(user_id=current_user.id).order_by(Transacao.data_vencimento.asc()).all()
    
    # Cálculo em tempo real dos KPIs
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
        'categoria': t.categoria_ref.nome if t.categoria_ref else 'Sem Categoria',
        'conciliado': t.conciliado
    } for t in transacoes]

    return jsonify({
        'transacoes': lista,
        'kpis': {
            'saldo_geral': saldo_geral,
            'a_receber': a_receber,
            'a_pagar': a_pagar
        }
    })

# 2. ALTERAR STATUS DE PAGAMENTO (BAIXA RÁPIDA)
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

# 3. GESTÃO DE CATEGORIAS E SUBCATEGORIAS
@finance_bp.route('/api/categorias', methods=['GET', 'POST'])
@login_required
def gerenciar_categorias():
    if request.method == 'POST':
        data = request.get_json()
        cat = Categoria(nome=data['nome'], tipo=data['tipo'], user_id=current_user.id)
        db.session.add(cat)
        db.session.commit()
        return jsonify({'success': True}), 201

    categorias = Categoria.query.filter_by(user_id=current_user.id).all()
    res = [{
        'id': c.id,
        'nome': c.nome,
        'tipo': c.tipo,
        'subcategorias': [{'id': s.id, 'nome': s.nome} for s.subcategorias in [c.subcategorias] for s in Subcategoria]
    } for c in categorias]
    return jsonify(res)

# 4. METAS ORÇAMENTÁRIAS (TETOS DE GASTO)
@finance_bp.route('/api/metas', methods=['GET', 'POST'])
@login_required
def gerenciar_metas():
    if request.method == 'POST':
        data = request.get_json()
        meta = MetaOrcamentaria(
            categoria_id=data['categoria_id'],
            teto_gasto=float(data['teto_gasto']),
            mes_ano=data['mes_ano'], # Ex: '2026-11'
            user_id=current_user.id
        )
        db.session.add(meta)
        db.session.commit()
        return jsonify({'success': True}), 201

    metas = MetaOrcamentaria.query.filter_by(user_id=current_user.id).all()
    resultado = []
    for m in metas:
        # Calcular gasto real da categoria no mês selecionado
        gastos = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.user_id == current_user.id,
            Transacao.categoria_id == m.categoria_id,
            Transacao.tipo == 'despesa',
            func.strftime('%Y-%m', Transacao.data_vencimento) == m.mes_ano
        ).scalar() or 0.0
        
        resultado.append({
            'id': m.id,
            'categoria_id': m.categoria_id,
            'teto_gasto': m.teto_gasto,
            'gasto_atual': gastos,
            'progresso_perc': round((gastos / m.teto_gasto) * 100, 2) if m.teto_gasto > 0 else 0
        })
    return jsonify(resultado)@finance_bp.route('/api/dashboard/analytics', methods=['GET'])
@login_required
def dashboard_analytics():
    # 1. Gráfico de Tendência (Evolução de Receitas vs Despesas)
    dados_mensais = db.session.query(
        func.strftime('%Y-%m', Transacao.data_vencimento).label('mes'),
        Transacao.tipo,
        func.sum(Transacao.valor).label('total')
    ).filter(Transacao.user_id == current_user.id)\
     .group_by('mes', Transacao.tipo)\
     .order_by('mes').all()

    meses = sorted(list(set([d.mes for d in dados_mensais])))
    receitas = [next((d.total for d in dados_mensais if d.mes == m and d.tipo == 'receita'), 0.0) for m in meses]
    despesas = [next((d.total for d in dados_mensais if d.mes == m and d.tipo == 'despesa'), 0.0) for m in meses]

    # 2. Gráfico de Distribuição por Categoria
    distribuicao = db.session.query(
        Categoria.nome,
        func.sum(Transacao.valor).label('total')
    ).join(Transacao, Transacao.categoria_id == Categoria.id)\
     .filter(Transacao.user_id == current_user.id, Transacao.tipo == 'despesa')\
     .group_by(Categoria.nome).all()

    cat_labels = [c.nome for c in distribuicao]
    cat_data = [c.total for c in distribuicao]

    return jsonify({
        'tendencia': {
            'labels': meses,
            'receitas': receitas,
            'despesas': despesas
        },
        'distribuicao': {
            'labels': cat_labels,
            'data': cat_data
        }
    })