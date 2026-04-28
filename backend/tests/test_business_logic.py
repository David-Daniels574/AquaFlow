from unittest.mock import Mock, patch

from flask_jwt_extended import create_access_token


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)
        self.content = b"payload"

    def json(self):
        return self._payload


@patch("booking_service.app.stripe.PaymentIntent.create")
def test_stripe_fractional_currency(mock_create, booking_app, booking_client):
    mock_create.return_value.client_secret = "pi_123_secret"

    with booking_app.app_context():
        token = create_access_token(identity="1", additional_claims={"role": "user"})

    response = booking_client.post(
        "/create-payment-intent",
        json={"amount": 1250.50, "booking_id": "BK-001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json["clientSecret"] == "pi_123_secret"

    called_args = mock_create.call_args[1]
    assert called_args["amount"] == 125050
    assert called_args["currency"] == "inr"


def test_stripe_minimum_charge(booking_app, booking_client):
    with booking_app.app_context():
        token = create_access_token(identity="1", additional_claims={"role": "user"})

    response = booking_client.post(
        "/create-payment-intent",
        json={"amount": 15.0, "booking_id": "BK-002"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "Invalid amount" in response.json["error"]


@patch("booking_service.app.requests.Session.request")
def test_tanker_booking_supplier_validation(mock_request, booking_app, booking_client):
    mock_request.return_value = FakeResponse(404, {"error": "Supplier not found"})

    with booking_app.app_context():
        token = create_access_token(identity="1", additional_claims={"role": "user"})

    response = booking_client.post(
        "/book_tanker",
        json={"supplier_id": 9999, "volume": 5000.0, "price": 2000.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "Supplier not found" in response.json["error"]


def test_challenge_completion_boundary(gamification_app, gamification_client):
    from gamification_service.models import Challenge, UserChallenge, db

    with gamification_app.app_context():
        challenge = Challenge(
            id=1,
            name="Save Water 101",
            short_desc="Save 100 liters of water",
            full_desc="Detailed instructions",
            eco_points=50,
            water_save_potential=100,
        )
        user_challenge = UserChallenge(id=1, user_id=1, challenge_id=1, progress=90.0, status="active")
        db.session.add_all([challenge, user_challenge])
        db.session.commit()
        token = create_access_token(identity="1", additional_claims={"role": "user"})

    response = gamification_client.put(
        "/update_challenge_progress/1",
        json={"progress": 100.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    with gamification_app.app_context():
        updated = db.session.get(UserChallenge, 1)
        assert updated.status == "completed"
        assert updated.eco_points_earned == 50
        assert updated.water_saved == 100


def test_society_bulk_order_rbac_normal_user(booking_app, booking_client):
    with booking_app.app_context():
        token = create_access_token(identity="1", additional_claims={"role": "user"})

    response = booking_client.post(
        "/society_bulk_order",
        json={"supplier_id": 1, "volume": 5000, "price": 2500, "society_id": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_correlation_id_echo(booking_app, booking_client):
    response = booking_client.get("/ping", headers={"X-Correlation-ID": "req-test-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "req-test-123"
