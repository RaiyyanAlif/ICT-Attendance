from getpass import getpass

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.teacher import Teacher


app = create_app()


with app.app_context():

    name = input("Teacher name: ").strip()
    email = input("Teacher email: ").strip().lower()
    department = input("Department: ").strip()

    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        exit()

    existing_teacher = Teacher.query.filter_by(
        email=email
    ).first()

    if existing_teacher:
        print("A teacher with this email already exists.")
        exit()

    teacher = Teacher(
        name=name,
        email=email,
        department=department,
        password_hash=generate_password_hash(password)
    )

    db.session.add(teacher)
    db.session.commit()

    print()
    print("Teacher account created successfully! ✅")