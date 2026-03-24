import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.config import settings


def create_admin():
    db = SessionLocal()

    try:
        admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if admin:
            print("Admin user already exists!")
            return

        if not settings.ADMIN_PASSWORD:
            print("ADMIN_PASSWORD is required to create the initial admin user.")
            return

        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            display_name="Administrator",
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )

        db.add(admin)
        db.commit()

        print("Admin user created successfully!")
        print(f"Username: {settings.ADMIN_USERNAME}")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
