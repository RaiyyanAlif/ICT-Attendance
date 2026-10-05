from app import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    # A student can exist in the master database
    # without being assigned to a batch yet.
    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("batches.id"),
        nullable=True
    )

    batch = db.relationship(
        "Batch",
        back_populates="students"
    )

    enrollments = db.relationship(
        "Enrollment",
        back_populates="student",
        lazy=True
    )

    attendance_records = db.relationship(
        "AttendanceRecord",
        back_populates="student",
        lazy=True
    )

    def __repr__(self):
        return f"<Student {self.student_id}>"