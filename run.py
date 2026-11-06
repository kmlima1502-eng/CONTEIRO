import os
from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    db_path = os.path.join(app.instance_path, 'database.db')
    
    # Se o banco antigo existir, força a remoção para recriar a estrutura correta sem Erro 500
    try:
        db.create_all()
    except Exception:
        if os.path.exists(db_path):
            os.remove(db_path)
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)