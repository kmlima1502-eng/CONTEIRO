import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua_chave_secreta_padrao')
    
    db_url = os.getenv('DATABASE_URL')
    
    # Ajusta o prefixo para usar o driver pg8000 compatível com a Render
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+pg8000://", 1)
        elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+pg8000://"):
            db_url = db_url.replace("postgresql://", "postgresql+pg8000://", 1)
            
    SQLALCHEMY_DATABASE_URI = db_url or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False