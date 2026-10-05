from app import db


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    student = db.relationship(
        "Student",
        back_populates="enrollments"
    )

    course = db.relationship(
        "Course",
        back_populates="enrollments"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "course_id",
            name="unique_student_course"
        ),
    )

    def __repr__(self):
        return (
            f"<Enrollment "
            f"student={self.student_id} "
            f"course={self.course_id}>"
        )