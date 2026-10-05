from app import db


class AttendanceSession(db.Model):
    __tablename__ = "attendance_sessions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teachers.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

    attendance_weight = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    course = db.relationship(
        "Course",
        back_populates="attendance_sessions"
    )

    teacher = db.relationship(
        "Teacher",
        back_populates="attendance_sessions"
    )

    records = db.relationship(
        "AttendanceRecord",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy=True
    )


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("attendance_sessions.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    present = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    marked_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    session = db.relationship(
        "AttendanceSession",
        back_populates="records"
    )

    student = db.relationship(
        "Student",
        back_populates="attendance_records"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "session_id",
            "student_id",
            name="unique_session_student"
        ),
    )