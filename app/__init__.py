import os
from flask import Flask
from app.models import db

def create_app():
    app = Flask(__name__)
    
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
        elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+pg8000://"):
            db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///' + os.path.join(app.instance_path, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app