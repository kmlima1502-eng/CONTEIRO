from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    db.create_all()
    # Tenta adicionar as colunas novas no SQLite da Render caso o banco já existisse
    try:
        db.session.execute(text("ALTER TABLE transacoes ADD COLUMN deletado BOOLEAN DEFAULT 0;"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE transacoes ADD COLUMN data_deletado DATETIME;"))
        db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    app.run(debug=True)