#!/usr/bin/env python3
"""Create admin user for AniFlix"""

import os
import sys
sys.path.append('.')

from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def create_admin_user():
    with app.app_context():
        # Check for existing admin users
        admin_users = User.query.filter(
            (User.email.like('%admin%')) | 
            (User.email.like('%@admin.aniflix.com'))
        ).all()
        
        if admin_users:
            print("Found existing admin users:")
            for user in admin_users:
                print(f"- Username: {user.username}, Email: {user.email}, Admin: {user.is_admin()}")
            
            # Update password for first admin user
            admin_user = admin_users[0]
            admin_user.password_hash = generate_password_hash("admin123")
            admin_user.email = "admin@admin.aniflix.com"  # Update email
            
            try:
                db.session.commit()
                print(f"✓ Admin user updated successfully!")
                print(f"Email: {admin_user.email}")
                print(f"Password: admin123")
                return
            except Exception as e:
                db.session.rollback()
                print(f"Error updating admin user: {e}")
        
        # Create new admin user with unique username
        admin_user = User()
        admin_user.username = "adminuser"  # Different username
        admin_user.email = "admin@admin.aniflix.com"
        admin_user.password_hash = generate_password_hash("admin123")
        admin_user.subscription_type = "vip_yearly"
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"✓ Admin user created successfully!")
            print(f"Email: {admin_user.email}")
            print(f"Password: admin123")
            print(f"Admin status: {admin_user.is_admin()}")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    create_admin_user()