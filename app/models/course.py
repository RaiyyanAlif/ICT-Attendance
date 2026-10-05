from app import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_code = db.Column(
        db.String(30),
        nullable=False
    )

    course_name = db.Column(
        db.String(150),
        nullable=False
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teachers.id"),
        nullable=False
    )

    # Every course belongs to exactly one batch
    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("batches.id"),
        nullable=True
    )

    # Academic session, e.g. 2026-2027
    academic_session = db.Column(
        db.String(20),
        nullable=True
    )

    teacher = db.relationship(
        "Teacher",
        back_populates="courses"
    )

    batch = db.relationship(
        "Batch",
        back_populates="courses"
    )

    enrollments = db.relationship(
        "Enrollment",
        back_populates="course",
        lazy=True
    )

    attendance_sessions = db.relationship(
        "AttendanceSession",
        back_populates="course",
        lazy=True
    )

    def __repr__(self):
        return f"<Course {self.course_code}>"