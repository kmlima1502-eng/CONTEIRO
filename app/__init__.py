import os
from flask import Flask
from config import Config
from app.models import db, User
from flask_login import LoginManager

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, '..'))
    
    # Garante que a pasta instance é criada automaticamente na raiz do projeto
    instance_path = os.path.join(project_root, 'instance')
    os.makedirs(instance_path, exist_ok=True)

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
        instance_path=instance_path
    )
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.finance import finance_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(finance_bp)

    with app.app_context():
        db.create_all()

    return app