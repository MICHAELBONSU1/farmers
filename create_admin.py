from app import app, db, User

with app.app_context():
    # Create admin user
    admin = User.query.filter_by(email='admin@farmerhub.com').first()
    if admin:
        admin.is_admin = True
        admin.is_active = True
        print('Admin already exists, updated!')
    else:
        admin = User(
            username='admin',
            email='admin@farmerhub.com',
            full_name='System Admin',
            location='Headquarters',
            farm_type='admin',
            is_admin=True,
            is_active=True,
            social_provider='local'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print('Admin created!')
    
    db.session.commit()
    print('Email: admin@farmerhub.com')
    print('Password: admin123')
