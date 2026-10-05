from flask_login import UserMixin
from werkzeug.security import check_password_hash

from app import db


class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    courses = db.relationship(
        "Course",
        back_populates="teacher",
        lazy=True
    )

    attendance_sessions = db.relationship(
        "AttendanceSession",
        back_populates="teacher",
        lazy=True
    )

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

    def __repr__(self):
        return f"<Teacher {self.email}>"