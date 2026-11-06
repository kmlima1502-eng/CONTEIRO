import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua_chave_secreta_padrao')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False