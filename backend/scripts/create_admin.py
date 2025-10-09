import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            display_name="Administrator",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        
        db.add(admin)
        db.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("\n⚠️  IMPORTANT: Please change the password after first login!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
