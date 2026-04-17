"""
Test script to verify login and signup functionality
"""
from app import app, db, User

# Create test context
with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
    # Check if test user exists
    test_email = "test@farmer.com"
    user = User.query.filter_by(email=test_email).first()
    
    if user:
        print(f"User found: {user.email}")
        print(f"Password hash: {user.password_hash[:50]}...")
        
        # Test password
        result = user.check_password("test123")
        print(f"Password check result: {result}")
    else:
        print("Creating test user...")
        user = User(
            username="testfarmer",
            email=test_email,
            full_name="Test Farmer",
            location="Test Location",
            farm_type="crop",
            social_provider="local"
        )
        user.set_password("test123")
        db.session.add(user)
        db.session.commit()
        print(f"Test user created: {user.email}")
        print(f"Password hash: {user.password_hash[:50]}...")
