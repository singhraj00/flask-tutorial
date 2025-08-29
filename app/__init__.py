from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_admin import Admin
import os 

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
admin = Admin(template_mode="bootstrap4")

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Folder auto create ho jayega agar na ho
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)

    login_manager.login_view = 'auth.login'

    # Import blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.services import services_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(services_bp)

    return app
