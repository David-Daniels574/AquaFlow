# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS  # Added for potential frontend integration
from config import Config
from models import db
from routes import api

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
jwt = JWTManager(app)
CORS(app)  # Enable CORS for all routes

app.register_blueprint(api, url_prefix='/api')

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5001)