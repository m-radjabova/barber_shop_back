from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    Assignment,
    AssignmentSubmission,
    Category,
    Course,
    Lesson,
    User,
)


def get_or_create(db, model, lookup: dict, create_data: dict):
    instance = db.query(model).filter_by(**lookup).first()
    if instance:
        return instance, False

    payload = {**lookup, **create_data}
    instance = model(**payload)
    db.add(instance)
    db.flush()
    return instance, True


def seed_data():
    db = SessionLocal()
    created = {
        "users": 0,
        "categories": 0,
        "courses": 0,
        "lessons": 0,
        "assignments": 0,
        "submissions": 0,
    }

    try:
        users_payload = [
            {
                "username": "student_demo",
                "email": "student_demo@example.com",
                "password": "DemoPass123",
                "roles": ["user"],
                "avatar": None,
            },
            {
                "username": "student_ali",
                "email": "student_ali@example.com",
                "password": "DemoPass123",
                "roles": ["user"],
                "avatar": None,
            },
            {
                "username": "student_lola",
                "email": "student_lola@example.com",
                "password": "DemoPass123",
                "roles": ["user"],
                "avatar": None,
            },
            {
                "username": "teacher_demo",
                "email": "teacher_demo@example.com",
                "password": "DemoPass123",
                "roles": ["teacher"],
                "avatar": None,
            },
            {
                "username": "admin_demo",
                "email": "admin_demo@example.com",
                "password": "DemoPass123",
                "roles": ["admin"],
                "avatar": None,
            },
        ]

        users = {}
        for item in users_payload:
            user, is_created = get_or_create(
                db,
                User,
                lookup={"username": item["username"]},
                create_data={
                    "email": item["email"],
                    "hashed_password": hash_password(item["password"]),
                    "roles": item["roles"],
                    "avatar": item["avatar"],
                },
            )
            users[item["username"]] = user
            created["users"] += int(is_created)

        categories_payload = [
            {
                "name": "Python Backend",
                "description": "FastAPI va PostgreSQL bo'yicha amaliy kurslar",
                "icon": None,
            },
            {
                "name": "Frontend React",
                "description": "React, TypeScript va API integratsiya",
                "icon": None,
            },
            {
                "name": "DevOps Basics",
                "description": "Docker, CI/CD va deploy asoslari",
                "icon": None,
            },
            {
                "name": "Data Engineering",
                "description": "ETL, Airflow va ma'lumotlar pipeline",
                "icon": None,
            },
            {
                "name": "Mobile Development",
                "description": "Flutter va mobil ilova arxitekturasi",
                "icon": None,
            },
        ]

        categories = {}
        for item in categories_payload:
            category, is_created = get_or_create(
                db,
                Category,
                lookup={"name": item["name"]},
                create_data={
                    "description": item["description"],
                    "icon": item["icon"],
                },
            )
            categories[item["name"]] = category
            created["categories"] += int(is_created)

        courses_payload = [
            {
                "category_name": "Python Backend",
                "title": "FastAPI Zero to Hero",
                "description": "REST API, auth va deploy mavzulari",
                "image": None,
                "level": "beginner",
                "price": 0,
                "duration": 480,
                "rating": 5,
            },
            {
                "category_name": "Frontend React",
                "title": "React Practical",
                "description": "Komponentlar, routing va state management",
                "image": None,
                "level": "intermediate",
                "price": 120,
                "duration": 600,
                "rating": 4,
            },
            {
                "category_name": "DevOps Basics",
                "title": "Docker from Scratch",
                "description": "Containerlar va production workflow",
                "image": None,
                "level": "beginner",
                "price": 90,
                "duration": 420,
                "rating": 5,
            },
            {
                "category_name": "Data Engineering",
                "title": "Airflow ETL Mastery",
                "description": "DAG, scheduler va ETL amaliyoti",
                "image": None,
                "level": "advanced",
                "price": 150,
                "duration": 700,
                "rating": 4,
            },
            {
                "category_name": "Mobile Development",
                "title": "Flutter App Builder",
                "description": "UI, state va API bilan ishlash",
                "image": None,
                "level": "intermediate",
                "price": 110,
                "duration": 560,
                "rating": 5,
            },
        ]

        courses = {}
        for item in courses_payload:
            category = categories[item["category_name"]]
            course, is_created = get_or_create(
                db,
                Course,
                lookup={"category_id": category.id, "title": item["title"]},
                create_data={
                    "description": item["description"],
                    "image": item["image"],
                    "level": item["level"],
                    "price": item["price"],
                    "duration": item["duration"],
                    "rating": item["rating"],
                },
            )
            courses[item["title"]] = course
            created["courses"] += int(is_created)

        lessons_payload = [
            {
                "course_title": "FastAPI Zero to Hero",
                "order": 1,
                "title": "Kirish va loyiha struktura",
                "description": "FastAPI asoslari va papka arxitekturasi",
                "is_free": True,
                "video_url": "https://example.com/videos/fastapi-1",
                "duration_sec": 900,
            },
            {
                "course_title": "React Practical",
                "order": 1,
                "title": "React Setup va JSX",
                "description": "Vite, JSX va birinchi komponent",
                "is_free": True,
                "video_url": "https://example.com/videos/react-1",
                "duration_sec": 840,
            },
            {
                "course_title": "Docker from Scratch",
                "order": 1,
                "title": "Docker Fundamentals",
                "description": "Image, container va Dockerfile",
                "is_free": False,
                "video_url": "https://example.com/videos/docker-1",
                "duration_sec": 960,
            },
            {
                "course_title": "Airflow ETL Mastery",
                "order": 1,
                "title": "Airflow Intro",
                "description": "DAG tushunchasi va scheduler",
                "is_free": False,
                "video_url": "https://example.com/videos/airflow-1",
                "duration_sec": 1020,
            },
            {
                "course_title": "Flutter App Builder",
                "order": 1,
                "title": "Flutter Widgets",
                "description": "Asosiy widgetlar va layout",
                "is_free": True,
                "video_url": "https://example.com/videos/flutter-1",
                "duration_sec": 930,
            }
        ]

        lessons = {}
        for item in lessons_payload:
            course = courses[item["course_title"]]
            lesson, is_created = get_or_create(
                db,
                Lesson,
                lookup={"course_id": course.id, "order": item["order"]},
                create_data={
                    "title": item["title"],
                    "description": item["description"],
                    "is_free": item["is_free"],
                    "video_url": item["video_url"],
                    "duration_sec": item["duration_sec"],
                },
            )
            lessons[f"{item['course_title']}#{item['order']}"] = lesson
            created["lessons"] += int(is_created)

        assignments_payload = [
            {
                "lesson_key": "FastAPI Zero to Hero#1",
                "order": 1,
                "title": "User CRUD endpoint yozish",
                "description": "GET/POST/PUT/DELETE endpointlarini yarating",
                "max_score": 100,
                "is_required": True,
                "due_days": 7,
            },
            {
                "lesson_key": "React Practical#1",
                "order": 1,
                "title": "Todo UI komponenti",
                "description": "Todo listni React state bilan yozing",
                "max_score": 100,
                "is_required": True,
                "due_days": 5,
            },
            {
                "lesson_key": "Docker from Scratch#1",
                "order": 1,
                "title": "Dockerfile yozish",
                "description": "Python app uchun optimal Dockerfile tayyorlang",
                "max_score": 100,
                "is_required": True,
                "due_days": 6,
            },
            {
                "lesson_key": "Airflow ETL Mastery#1",
                "order": 1,
                "title": "Oddiy DAG yaratish",
                "description": "3 taskdan iborat DAG yozing",
                "max_score": 100,
                "is_required": False,
                "due_days": 8,
            },
            {
                "lesson_key": "Flutter App Builder#1",
                "order": 1,
                "title": "Login sahifasi UI",
                "description": "Flutter'da login ekranini chizing",
                "max_score": 100,
                "is_required": True,
                "due_days": 4,
            },
        ]

        assignments = []
        for item in assignments_payload:
            lesson = lessons[item["lesson_key"]]
            assignment, is_created = get_or_create(
                db,
                Assignment,
                lookup={"lesson_id": lesson.id, "order": item["order"]},
                create_data={
                    "title": item["title"],
                    "description": item["description"],
                    "due_at": datetime.now(timezone.utc) + timedelta(days=item["due_days"]),
                    "max_score": item["max_score"],
                    "is_required": item["is_required"],
                },
            )
            assignments.append(assignment)
            created["assignments"] += int(is_created)

        submission_targets = [
            ("student_demo", 0),
            ("student_ali", 1),
            ("student_lola", 2),
            ("student_demo", 3),
            ("student_ali", 4),
        ]

        for idx, (username, assignment_index) in enumerate(submission_targets, start=1):
            assignment = assignments[assignment_index]
            user = users[username]
            _, is_created = get_or_create(
                db,
                AssignmentSubmission,
                lookup={"assignment_id": assignment.id, "user_id": user.id},
                create_data={
                    "text_answer": f"Submission #{idx} by {username}",
                    "file_url": None,
                    "status": "submitted",
                    "score": None,
                },
            )
            created["submissions"] += int(is_created)

        db.commit()

        print("Seed yakunlandi.")
        print(f"Yaratildi: {created}")
        print("Demo loginlar:")
        print("- student_demo / DemoPass123")
        print("- student_ali / DemoPass123")
        print("- student_lola / DemoPass123")
        print("- teacher_demo / DemoPass123")
        print("- admin_demo / DemoPass123")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
