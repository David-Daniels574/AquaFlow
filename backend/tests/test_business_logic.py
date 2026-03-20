import pytest
from unittest.mock import patch
from flask_jwt_extended import create_access_token

# Import db directly from app.py
from app import db 

# Import models directly from models.py
from models import User, TankerListing, TankerOrder, Challenge, UserChallenge
from app import app as flask_app

# ==========================================
# PART A: FINANCIAL & STRIPE TESTS
# ==========================================

@patch('stripe.PaymentIntent.create') 
def test_stripe_fractional_currency(mock_stripe, client):
    """Test A.1: Ensures exact fractional amounts are converted to paise."""
    mock_stripe.return_value.client_secret = "pi_123_secret"
    
    with flask_app.app_context():
        # Generate valid token to prevent 422 Unprocessable Entity
        access_token = create_access_token(identity=str(1), additional_claims={"role": "user"})
    
    # User books a tanker costing ₹1250.50
    payload = {"amount": 1250.50, "booking_id": "BK-001"}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = client.post('/api/create-payment-intent', json=payload, headers=headers)
    assert response.status_code == 200
    
    # Assert Jenkins/Pytest caught the correct math (1250.50 * 100)
    mock_stripe.assert_called_once()
    called_args = mock_stripe.call_args[1]
    assert called_args['amount'] == 125050
    assert called_args['currency'] == 'inr'

def test_stripe_minimum_charge(client):
    """Test A.2: Ensures API rejects amounts < 40 INR before hitting Stripe."""
    with flask_app.app_context():
        access_token = create_access_token(identity=str(1), additional_claims={"role": "user"})
        
    payload = {"amount": 15.00, "booking_id": "BK-002"}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = client.post('/api/create-payment-intent', json=payload, headers=headers)
    
    # Assuming you added validation: if amount < 40: return 400
    assert response.status_code == 400

# ==========================================
# PART B: STATE MACHINE & LOGIC TESTS
# ==========================================

def test_tanker_availability_lock(client): 
    """Test B.1: Prevent double-booking a tanker."""
    with flask_app.app_context():
        access_token = create_access_token(identity=str(1), additional_claims={"role": "user"})
        
        # Seed a dummy tanker using the exact fields from your model
        tanker = TankerListing(
            id=1, 
            owner_id=1, 
            vehicle_number="MH-12-TEST-9999", 
            capacity=5000.0, 
            price_per_liter=0.4, 
            status='booked'
        )
        db.session.add(tanker)
        db.session.commit()

    payload = {"tanker_id": 1, "delivery_date": "2026-10-10"}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = client.post('/api/book_tanker', json=payload, headers=headers)
    
    # Should fail because it's not 'available'
    assert response.status_code in [400, 404]
    assert b"available" in response.data.lower()

def test_challenge_completion_boundary(client): 
    """Test B.2: Progress hitting 100% triggers completion and points."""
    with flask_app.app_context(): 
        access_token = create_access_token(identity=str(1), additional_claims={"role": "user"})
        
        # Seed active challenge at 90% (added the missing 'name' field)
        uc = UserChallenge(id=1, user_id=1, challenge_id=1, progress=90.0, status='active')
        chal = Challenge(id=1, name="Save Water 101", eco_points=50, water_save_potential=100)
        db.session.add_all([uc, chal])
        db.session.commit()

    payload = {"progress": 100.0}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = client.put('/api/update_challenge_progress/1', json=payload, headers=headers)
    
    assert response.status_code == 200
    
    # Verify State Change inside app context
    with flask_app.app_context():
        updated_uc = UserChallenge.query.get(1)
        assert updated_uc.status == 'completed'
        assert updated_uc.eco_points_earned == 50
        assert updated_uc.water_saved == 100

# ==========================================
# PART C: RBAC ENFORCEMENT TESTS
# ==========================================

def test_society_bulk_order_rbac_normal_user(client):
    """Test C.1: Normal user tries to use Society Admin route."""
    with flask_app.app_context():
        # Generate token with normal 'user' role
        access_token = create_access_token(identity=str(1), additional_claims={"role": "user"})
        
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {"supplier_id": 1, "volume": 5000, "price": 2500, "society_id": 1}
    
    response = client.post('/api/society_bulk_order', json=payload, headers=headers)
    
    # Must be 403 Forbidden since role is not admin
    assert response.status_code == 403