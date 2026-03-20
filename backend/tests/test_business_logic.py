import pytest
from unittest.mock import patch
from app import db
# Adjust these imports to match your actual model names
from app.models import User, TankerListing, TankerOrder, Challenge, UserChallenge

# ==========================================
# PART A: FINANCIAL & STRIPE TESTS
# ==========================================

@patch('app.routes.stripe.PaymentIntent.create')
def test_stripe_fractional_currency(mock_stripe, client):
    """Test A.1: Ensures exact fractional amounts are converted to paise."""
    mock_stripe.return_value.client_secret = "pi_123_secret"
    
    # User books a tanker costing ₹1250.50
    payload = {"amount": 1250.50, "booking_id": "BK-001"}
    headers = {'Authorization': f'Bearer MOCK_JWT_TOKEN_USER'}
    
    response = client.post('/create-payment-intent', json=payload, headers=headers)
    assert response.status_code == 200
    
    # Assert Jenkins/Pytest caught the correct math (1250.50 * 100)
    mock_stripe.assert_called_once()
    called_args = mock_stripe.call_args[1]
    assert called_args['amount'] == 125050
    assert called_args['currency'] == 'inr'

def test_stripe_minimum_charge(client):
    """Test A.2: Ensures API rejects amounts < 40 INR before hitting Stripe."""
    payload = {"amount": 15.00, "booking_id": "BK-002"}
    headers = {'Authorization': f'Bearer MOCK_JWT_TOKEN_USER'}
    
    response = client.post('/create-payment-intent', json=payload, headers=headers)
    
    # Assuming you added validation: if amount < 40: return 400
    assert response.status_code == 400

# ==========================================
# PART B: STATE MACHINE & LOGIC TESTS
# ==========================================

def test_tanker_availability_lock(client, app_context):
    """Test B.1: Prevent double-booking a tanker."""
    # Seed a dummy tanker that is already booked
    tanker = TankerListing(id=1, supplier_id=1, volume=5000, price=2000, status='booked')
    db.session.add(tanker)
    db.session.commit()

    payload = {"tanker_id": 1, "delivery_date": "2026-10-10"}
    headers = {'Authorization': f'Bearer MOCK_JWT_TOKEN_USER'}
    
    response = client.post('/book_tanker', json=payload, headers=headers)
    
    # Should fail because it's not 'available'
    assert response.status_code in [400, 404]
    assert b"available" in response.data.lower()

def test_challenge_completion_boundary(client, app_context):
    """Test B.2: Progress hitting 100% triggers completion and points."""
    # Seed active challenge at 90%
    uc = UserChallenge(id=1, user_id=1, challenge_id=1, progress=90.0, status='active')
    chal = Challenge(id=1, eco_points=50, water_save_potential=100)
    db.session.add_all([uc, chal])
    db.session.commit()

    payload = {"progress": 100.0}
    headers = {'Authorization': f'Bearer MOCK_JWT_TOKEN_USER_1'}
    
    response = client.put('/update_challenge_progress/1', json=payload, headers=headers)
    
    assert response.status_code == 200
    
    # Verify State Change
    updated_uc = UserChallenge.query.get(1)
    assert updated_uc.status == 'completed'
    assert updated_uc.eco_points_earned == 50
    assert updated_uc.water_saved == 100

# ==========================================
# PART C: RBAC ENFORCEMENT TESTS
# ==========================================

def test_society_bulk_order_rbac_normal_user(client):
    """Test C.1: Normal user tries to use Society Admin route."""
    # Simulating a JWT token payload where role == 'user'
    headers = {'Authorization': f'Bearer MOCK_JWT_TOKEN_NORMAL_USER'}
    payload = {"supplier_id": 1, "volume": 5000, "price": 2500, "society_id": 1}
    
    response = client.post('/society_bulk_order', json=payload, headers=headers)
    
    # Must be 403 Forbidden
    assert response.status_code == 403