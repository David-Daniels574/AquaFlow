# backend/config.py
from dotenv import load_dotenv
import os

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Application configuration class.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    
    # Docker injects DATABASE_URL. 
    # Fallback to SQLite only if the ENV var is missing (local dev without docker)
    uri = os.environ.get('DATABASE_URL')
    
    # Fix for SQLAlchemy 1.4+ which requires 'postgresql://' instead of 'postgres://'
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = uri or 'sqlite:///' + os.path.join(basedir, 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key'
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or "redis://redis:6379/0"
    CACHE_DEFAULT_TIMEOUT = 300  # Default cache life: 5 minutes