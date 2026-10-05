from app import db


class Batch(db.Model):
    __tablename__ = "batches"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=True
    )

    academic_session = db.Column(
        db.String(20),
        nullable=True
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    students = db.relationship(
        "Student",
        back_populates="batch",
        lazy=True
    )

    courses = db.relationship(
        "Course",
        back_populates="batch",
        lazy=True
    )

    def __repr__(self):
        return f"<Batch {self.name}>"