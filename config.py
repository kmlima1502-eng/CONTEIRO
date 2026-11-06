import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua_chave_secreta_padrao')
    
    # 1. Lê a variável DATABASE_URL fornecida pela Render (PostgreSQL)
    db_url = os.getenv('DATABASE_URL')
    
    # 2. Correção de compatibilidade: o SQLAlchemy 2.0 exige 'postgresql://' em vez de 'postgres://'
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    # 3. Se estiver na Render usa o PostgreSQL; se estiver rodando localmente usa o SQLite
    SQLALCHEMY_DATABASE_URI = db_url or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'database.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False