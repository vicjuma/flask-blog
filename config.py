from dotenv import load_dotenv
import os
import wsgiref

load_dotenv()


class Config(object):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.sqlite'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEBUG = True
    MAIL_PORT = 587
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_MAX_EMAILS = 3000
    SECRET_KEY = '49b2ff2ae97b7c12'
    MAIL_SUPPRESS_SEND = True
    MAIL_ASCCI_ATTACHMENTS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    TEMPLATES_AUTO_RELOAD = True


class DevelopmentConfig(Config):
    pass


class ProductionConfig(Config):
    MAIL_DEBUG = False
    DEBUG = False


class TestingConfig(Config):
    pass

