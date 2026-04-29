from dotenv import load_dotenv

load_dotenv(override=True)

import os
from datetime import time

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.services.user_service import UserService


BARBERS = [
    {
        "full_name": "Jamshid Xasanov",
        "email": "jamshid@gmail.com",
        "password": "123456",
        "avatar": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=900&q=80",
        "specialty": "Skin fade va zamonaviy erkaklar sochi",
        "bio": "Aniq chiziqlar va toza fade bilan ishlaydi. Tez va tartibli servis beradi.",
        "location_text": "Chilonzor, Toshkent",
        "work_start_time": time(9, 0),
        "work_end_time": time(19, 0),
        "services": [
            {"name": "Classic Haircut", "price": 70000, "duration_minutes": 45},
            {"name": "Beard Styling", "price": 50000, "duration_minutes": 30},
        ],
    },
    {
        "full_name": "Azizbek Qodirov",
        "email": "azizbek@gmail.com",
        "password": "123456",
        "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80",
        "specialty": "Mid fade va beard trim",
        "bio": "Sokin uslubda ishlaydi, beard va haircut kombinatsiyalariga kuchli.",
        "location_text": "Yunusobod, Toshkent",
        "work_start_time": time(10, 0),
        "work_end_time": time(20, 0),
        "services": [
            {"name": "Fade Cut", "price": 80000, "duration_minutes": 50},
            {"name": "Haircut + Beard", "price": 110000, "duration_minutes": 70},
        ],
    },
    {
        "full_name": "Bekzod Rahimov",
        "email": "bekzod@gmail.com",
        "password": "123456",
        "avatar": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80",
        "specialty": "Classic va premium scissors cut",
        "bio": "Qaychi bilan ishlashni yaxshi ko‘radi. Business style mijozlar uchun mos.",
        "location_text": "Mirzo Ulug‘bek, Toshkent",
        "work_start_time": time(8, 30),
        "work_end_time": time(18, 30),
        "services": [
            {"name": "Scissors Cut", "price": 90000, "duration_minutes": 60},
            {"name": "Kids Haircut", "price": 60000, "duration_minutes": 35},
        ],
    },
    {
        "full_name": "Sardor Tursunov",
        "email": "sardor@gmail.com",
        "password": "123456",
        "avatar": "https://images.unsplash.com/photo-1504257432389-52343af06ae3?auto=format&fit=crop&w=900&q=80",
        "specialty": "Textured crop va buzz cut",
        "bio": "Minimalistik va toza uslublarga ixtisoslashgan. Yoshlar orasida ommabop.",
        "location_text": "Olmazor, Toshkent",
        "work_start_time": time(11, 0),
        "work_end_time": time(21, 0),
        "services": [
            {"name": "Buzz Cut", "price": 50000, "duration_minutes": 25},
            {"name": "Textured Crop", "price": 85000, "duration_minutes": 55},
        ],
    },
    {
        "full_name": "Doston Ergashev",
        "email": "doston@gmail.com",
        "password": "123456",
        "avatar": "https://images.unsplash.com/photo-1504593811423-6dd665756598?auto=format&fit=crop&w=900&q=80",
        "specialty": "Hot towel shave va premium parvarish",
        "bio": "An’anaviy barbering elementlarini zamonaviy servis bilan birlashtiradi.",
        "location_text": "Shayxontohur, Toshkent",
        "work_start_time": time(9, 30),
        "work_end_time": time(19, 30),
        "services": [
            {"name": "Hot Towel Shave", "price": 75000, "duration_minutes": 40},
            {"name": "Premium Grooming", "price": 120000, "duration_minutes": 75},
        ],
    },
    {
        "full_name": "Temur Malikov",
        "email": "temur@gmail.com",
        "password": "123456",
        "avatar": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=900&q=80",
        "specialty": "Low taper va styling",
        "bio": "Soch turiga qarab individual tavsiya beradi. Styling finishlari kuchli.",
        "location_text": "Sergeli, Toshkent",
        "work_start_time": time(10, 30),
        "work_end_time": time(20, 30),
        "services": [
            {"name": "Low Taper", "price": 85000, "duration_minutes": 50},
            {"name": "Hair Styling", "price": 45000, "duration_minutes": 20},
        ],
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        user_service = UserService(db)
        admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
        admin_full_name = os.getenv("ADMIN_FULL_NAME", "Admin").strip()

        if admin_email and admin_password:
            existing_admin = db.query(User).filter(User.email == admin_email).first()
            if existing_admin:
                print("Admin allaqachon mavjud")
            else:
                user_service.create_admin(admin_full_name, admin_email, admin_password)
                print("Admin yaratildi")
        else:
            print("ADMIN_EMAIL yoki ADMIN_PASSWORD .env ichida topilmadi, admin skip qilindi")

        created_barbers = 0
        existing_barbers = 0
        for barber_data in BARBERS:
            existing_barber = db.query(User).filter(User.email == barber_data["email"]).first()
            if existing_barber:
                existing_barber.password_hash = hash_password(barber_data["password"])
                db.add(existing_barber)
                db.commit()
                existing_barbers += 1
                continue

            barber = user_service._create_user(
                full_name=barber_data["full_name"],
                email=barber_data["email"],
                password=barber_data["password"],
                role=UserRole.BARBER,
            )
            barber.avatar = barber_data["avatar"]
            barber.specialty = barber_data["specialty"]
            barber.bio = barber_data["bio"]
            barber.location_text = barber_data["location_text"]
            barber.work_start_time = barber_data["work_start_time"]
            barber.work_end_time = barber_data["work_end_time"]
            barber.services = barber_data["services"]
            barber.is_active = True
            db.add(barber)
            db.commit()
            created_barbers += 1

        print(f"{created_barbers} ta barber yaratildi, {existing_barbers} tasi avvaldan bor edi")
    finally:
        db.close()


if __name__ == "__main__":
    main()
