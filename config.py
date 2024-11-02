import os
from dotenv import load_dotenv

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'times-travel-salt'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    load_dotenv()  # Load environment variables from .env file

    MAIL_SERVER = 'mail.booksaudiservices.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'info@booksaudiservices.com'
    MAIL_PASSWORD = 'Timestravel567#'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEFAULT_SENDER = 'info@booksaudiservices.com'