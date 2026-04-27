from dotenv import load_dotenv

load_dotenv(override=True)

import os

from app.core.database import SessionLocal
from app.models.user import User
from app.services.user_service import UserService


def main() -> None:
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
        admin_full_name = os.getenv("ADMIN_FULL_NAME", "Admin").strip()

        if not admin_email or not admin_password:
            print("ADMIN_EMAIL yoki ADMIN_PASSWORD .env ichida topilmadi")
            return

        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            print("Admin allaqachon mavjud")
            return

        UserService(db).create_admin(admin_full_name, admin_email, admin_password)
        print("Admin yaratildi")
    finally:
        db.close()


if __name__ == "__main__":
    main()
