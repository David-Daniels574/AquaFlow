import time
import os
import psycopg2
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError
from config import Config
from models import db,cache
from routes import api

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
cache.init_app(app)
jwt = JWTManager(app)
CORS(app)

app.register_blueprint(api, url_prefix='/api')

def wait_for_db():
    """
    DC Concept: Fault Tolerance / Retry Pattern.
    Wait for the database container to become ready before proceeding.
    """
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        print("Checking database connection...")
        retries = 5
        while retries > 0:
            try:
                conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
                conn.close()
                print("Database is ready!")
                return
            except psycopg2.OperationalError:
                print(f"Database not ready. Waiting 2 seconds... ({retries} retries left)")
                time.sleep(2)
                retries -= 1
        print("WARNING: Could not connect to Database after retries.")

# Create database tables if they don't exist
with app.app_context():
    # Block startup until DB is ready
    wait_for_db()
    
    # --- FIX FOR RACE CONDITION ---
    try:
        # Note: In a real production DC system, use Flask-Migrate (Alembic)
        db.create_all()
        print("Tables created successfully (or already existed).")
    except (OperationalError, ProgrammingError):
        # If another worker created the table while we were trying, 
        # the DB will throw an error. We safely ignore it here.
        print("Database tables already exist (Race Condition handled).")

if __name__ == '__main__':
    # Use 0.0.0.0 to be accessible outside the container
    app.run(debug=True, host='0.0.0.0', port=5001)