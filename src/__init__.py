from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from dotenv import load_dotenv
from datetime import datetime
from flask_mail import Mail, Message

db = SQLAlchemy()
mail = Mail()

def create_app(config_class='config.Config'):
    app = Flask(__name__)

    if app.config['ENV'] == 'Production':
        app.config.from_object('config.ProductionConfig')
    elif app.config['ENV'] == 'development':
        app.config.from_object('config.DEvelopmentConfig')
    elif app.config['ENV'] == 'testing':
        app.config.from_object('config.TestingConfig')
    else:
        app.config.from_object('config.Config')


    db.init_app(app)
    mail.init_app(app)



    from src.admin import admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from src.views import views_blueprint

    app.register_blueprint(views_blueprint, url_prefix='/users')

    return app