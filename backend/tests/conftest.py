import pytest
from app import app, db # Import your Flask app and db instance

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # You would optionally insert seed data here (e.g., a dummy user)
            yield client
            db.session.remove()
            db.drop_all()