from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from flask_jwt_extended import JWTManager
from flask_cors import CORS

load_dotenv()

db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret')
    
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from app.routes import auth_bp, user_bp, book_search_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(book_search_bp, url_prefix='/books')

    CORS(app)
    
    DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    @app.route('/downloads/<filename>')
    def download_file(filename):
        return send_from_directory(DOWNLOAD_DIR, filename)
    
    return app
