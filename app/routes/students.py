from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.models.student import Student
from app.models.batch import Batch
from app.models.course import Course
from app.models.enrollment import Enrollment


students_bp = Blueprint(
    "students",
    __name__,
    url_prefix="/students"
)


# =========================================================
# STUDENT LIST
# =========================================================

@students_bp.route("/")
@login_required
def list_students():

    students = (
        Student.query
        .order_by(Student.student_id.asc())
        .all()
    )

    return render_template(
        "students/list.html",
        students=students
    )


# =========================================================
# ADD STUDENT
# =========================================================

@students_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_student():

    batch_id = request.args.get(
        "batch_id",
        type=int
    )

    course_id = request.args.get(
        "course_id",
        type=int
    )

    course = None
    batch = None

    # =====================================================
    # COURSE MODE
    # =====================================================

    if course_id:

        course = db.session.get(
            Course,
            course_id
        )

        if not course:
            return "Course not found", 404

        if course.teacher_id != current_user.id:
            return "Unauthorized", 403

        if not course.batch_id:
            return (
                "This course has no batch assigned yet.",
                400
            )

        batch = course.batch

        if not batch:
            return "Course batch not found.", 400

        # The course determines the batch.
        batch_id = course.batch_id

    # =====================================================
    # BATCH MODE
    # =====================================================

    elif batch_id:

        batch = db.session.get(
            Batch,
            batch_id
        )

        if not batch:
            return "Batch not found", 404

    # =====================================================
    # NO CONTEXT
    # =====================================================

    else:

        return (
            "Please open Add Student from a specific "
            "batch or course.",
            400
        )

    # =====================================================
    # POST REQUEST
    # =====================================================

    if request.method == "POST":

        student_id = request.form.get(
            "student_id",
            ""
        ).strip().upper()

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        # =================================================
        # COURSE MODE
        # =================================================

        if course:

            # Never trust a submitted batch ID.
            # The course determines the batch.

            batch_id = course.batch_id

        # =================================================
        # BATCH MODE
        # =================================================

        else:

            submitted_batch_id = request.form.get(
                "batch_id",
                type=int
            )

            if submitted_batch_id != batch.id:

                return render_template(
                    "students/add.html",
                    batch=batch,
                    course=course,
                    error="Invalid batch selection."
                )

            batch_id = batch.id

        # =================================================
        # VALIDATE BATCH
        # =================================================

        batch = db.session.get(
            Batch,
            batch_id
        )

        if not batch:

            return render_template(
                "students/add.html",
                batch=batch,
                course=course,
                error="Invalid batch."
            )

        # =================================================
        # VALIDATE STUDENT ID
        # =================================================

        if not student_id:

            return render_template(
                "students/add.html",
                batch=batch,
                course=course,
                error="Student ID is required."
            )

        # =================================================
        # VALIDATE NAME
        # =================================================

        if not name:

            return render_template(
                "students/add.html",
                batch=batch,
                course=course,
                error="Student name is required."
            )

        # =================================================
        # DEFAULT EMAIL
        # =================================================

        if not email:

            email = (
                f"{student_id.lower()}"
                "@mbstu.ac.bd"
            )

        # =================================================
        # CHECK EXISTING STUDENT
        # =================================================

        existing_student = Student.query.filter_by(
            student_id=student_id
        ).first()

        if existing_student:

            # ---------------------------------------------
            # STUDENT BELONGS TO ANOTHER BATCH
            # ---------------------------------------------

            if existing_student.batch_id != batch.id:

                return render_template(
                    "students/add.html",
                    batch=batch,
                    course=course,
                    error=(
                        f"{student_id} already belongs to "
                        f"another batch "
                        f"({existing_student.batch.name})."
                    )
                )

            # ---------------------------------------------
            # COURSE MODE
            # ---------------------------------------------

            if course:

                # Final safety check.
                if existing_student.batch_id != course.batch_id:

                    return render_template(
                        "students/add.html",
                        batch=batch,
                        course=course,
                        error=(
                            "This student's batch does not "
                            "match the course batch."
                        )
                    )

                # Check existing enrollment.
                existing_enrollment = Enrollment.query.filter_by(
                    student_id=existing_student.id,
                    course_id=course.id
                ).first()

                if existing_enrollment:

                    return render_template(
                        "students/add.html",
                        batch=batch,
                        course=course,
                        error=(
                            "This student is already "
                            "enrolled in this course."
                        )
                    )

                # Create enrollment.
                enrollment = Enrollment(
                    student_id=existing_student.id,
                    course_id=course.id
                )

                db.session.add(enrollment)
                db.session.commit()

                return redirect(
                    url_for(
                        "courses.course_details",
                        course_id=course.id
                    )
                )

            # ---------------------------------------------
            # BATCH MODE
            # ---------------------------------------------

            return render_template(
                "students/add.html",
                batch=batch,
                course=course,
                error=(
                    "This student already exists "
                    "in this batch."
                )
            )

        # =================================================
        # CHECK DUPLICATE EMAIL
        # =================================================

        existing_email = Student.query.filter_by(
            email=email
        ).first()

        if existing_email:

            return render_template(
                "students/add.html",
                batch=batch,
                course=course,
                error=(
                    "This email address is already "
                    "associated with another student."
                )
            )

        # =================================================
        # CREATE NEW STUDENT
        # =================================================

        student = Student(
            student_id=student_id,
            name=name,
            email=email,
            batch_id=batch.id
        )

        db.session.add(student)

        # Generate student.id before enrollment.
        db.session.flush()

        # =================================================
        # COURSE MODE
        # AUTOMATIC ENROLLMENT
        # =================================================

        if course:

            # Final backend protection.
            if student.batch_id != course.batch_id:

                db.session.rollback()

                return render_template(
                    "students/add.html",
                    batch=batch,
                    course=course,
                    error=(
                        "Student batch does not match "
                        "course batch."
                    )
                )

            enrollment = Enrollment(
                student_id=student.id,
                course_id=course.id
            )

            db.session.add(enrollment)

        # =================================================
        # SAVE
        # =================================================

        db.session.commit()

        # =================================================
        # REDIRECT
        # =================================================

        if course:

            return redirect(
                url_for(
                    "courses.course_details",
                    course_id=course.id
                )
            )

        return redirect(
            url_for(
                "batches.batch_students",
                batch_id=batch.id
            )
        )

    # =====================================================
    # GET REQUEST
    # =====================================================

    return render_template(
        "students/add.html",
        batch=batch,
        course=course
    )


# =========================================================
# EDIT STUDENT
# =========================================================

@students_bp.route(
    "/<int:student_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_student(student_id):

    student = db.session.get(
        Student,
        student_id
    )

    if not student:
        return "Student not found", 404

    if request.method == "POST":

        new_student_id = request.form.get(
            "student_id",
            ""
        ).strip().upper()

        new_name = request.form.get(
            "name",
            ""
        ).strip()

        new_email = request.form.get(
            "email",
            ""
        ).strip().lower()

        # =================================================
        # VALIDATE STUDENT ID
        # =================================================

        if not new_student_id:

            return render_template(
                "students/edit.html",
                student=student,
                error="Student ID is required."
            )

        # =================================================
        # VALIDATE NAME
        # =================================================

        if not new_name:

            return render_template(
                "students/edit.html",
                student=student,
                error="Student name is required."
            )

        # =================================================
        # DEFAULT EMAIL
        # =================================================

        if not new_email:

            new_email = (
                f"{new_student_id.lower()}"
                "@mbstu.ac.bd"
            )

        # =================================================
        # DUPLICATE STUDENT ID
        # =================================================

        duplicate_id = Student.query.filter(
            Student.student_id == new_student_id,
            Student.id != student.id
        ).first()

        if duplicate_id:

            return render_template(
                "students/edit.html",
                student=student,
                error=(
                    "Another student already uses "
                    "this Student ID."
                )
            )

        # =================================================
        # DUPLICATE EMAIL
        # =================================================

        duplicate_email = Student.query.filter(
            Student.email == new_email,
            Student.id != student.id
        ).first()

        if duplicate_email:

            return render_template(
                "students/edit.html",
                student=student,
                error=(
                    "Another student already uses "
                    "this email address."
                )
            )

        # =================================================
        # UPDATE
        # =================================================

        student.student_id = new_student_id
        student.name = new_name
        student.email = new_email

        db.session.commit()

        return redirect(
            url_for(
                "batches.batch_students",
                batch_id=student.batch_id
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "students/edit.html",
        student=student
    )