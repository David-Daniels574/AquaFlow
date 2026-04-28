import os
import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _base_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key-at-least-32-chars")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "test-internal-token")
    monkeypatch.setenv("SERVICE_TIMEOUT_SECONDS", "1")


@pytest.fixture
def booking_app(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SUPPLIER_SERVICE_URL", "http://supplier-service.invalid")
    monkeypatch.setenv("AUTH_SERVICE_URL", "http://auth-service.invalid")

    from booking_service.app import create_app
    from booking_service.models import db

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def booking_client(booking_app):
    return booking_app.test_client()


@pytest.fixture
def gamification_app(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("AUTH_SERVICE_URL", "http://auth-service.invalid")

    from gamification_service.app import create_app
    from gamification_service.models import db

    app = create_app()
    app.config["TESTING"] = True

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def gamification_client(gamification_app):
    return gamification_app.test_client()
