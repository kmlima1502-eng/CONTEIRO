import os
from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # 1. Garante a criação de tabelas novas
    db.create_all()
    
    # 2. Executa a migração forçada de colunas em falta no SQLite da Render
    colunas_para_adicionar = [
        "ALTER TABLE users ADD COLUMN criado_em DATETIME;",
        "ALTER TABLE transacoes ADD COLUMN deletado BOOLEAN DEFAULT 0;",
        "ALTER TABLE transacoes ADD COLUMN data_deletado DATETIME;"
    ]
    
    for comando in colunas_para_adicionar:
        try:
            db.session.execute(text(comando))
            db.session.commit()
        except Exception:
            db.session.rollback()

if __name__ == '__main__':
    app.run(debug=True)