from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)

from flask_login import login_required

from app import db
from app.models.batch import Batch
from app.models.student import Student
from app.models.course import Course


batches_bp = Blueprint(
    "batches",
    __name__,
    url_prefix="/batches"
)


# =========================================================
# BATCH LIST
# =========================================================

@batches_bp.route("/")
@login_required
def list_batches():

    batches = (
        Batch.query
        .order_by(Batch.name.asc())
        .all()
    )

    batch_counts = {}

    for batch in batches:

        batch_counts[batch.id] = (
            Student.query
            .filter_by(batch_id=batch.id)
            .count()
        )

    return render_template(
        "batches/list.html",
        batches=batches,
        batch_counts=batch_counts
    )


# =========================================================
# ADD BATCH
# =========================================================

@batches_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
def add_batch():

    if request.method == "POST":

        name = (
            request.form.get("name", "")
            .strip()
        )

        department = (
            request.form.get("department", "")
            .strip()
        )

        academic_session = (
            request.form.get(
                "academic_session",
                ""
            )
            .strip()
        )

        if not name:
            return render_template(
                "batches/add.html",
                error="Batch name is required."
            )

        if not academic_session:
            return render_template(
                "batches/add.html",
                error="Academic session is required."
            )

        existing_batch = (
            Batch.query
            .filter_by(name=name)
            .first()
        )

        if existing_batch:
            return render_template(
                "batches/add.html",
                error=(
                    "A batch with this name "
                    "already exists."
                )
            )

        batch = Batch(
            name=name,
            department=department or None,
            academic_session=academic_session,
            is_active=True
        )

        db.session.add(batch)
        db.session.commit()

        return redirect(
            url_for("batches.list_batches")
        )

    return render_template(
        "batches/add.html"
    )


# =========================================================
# EDIT BATCH
# =========================================================

@batches_bp.route(
    "/<int:batch_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_batch(batch_id):

    batch = db.session.get(
        Batch,
        batch_id
    )

    if not batch:
        return "Batch not found", 404

    if request.method == "POST":

        name = (
            request.form.get("name", "")
            .strip()
        )

        department = (
            request.form.get("department", "")
            .strip()
        )

        academic_session = (
            request.form.get(
                "academic_session",
                ""
            )
            .strip()
        )

        if not name:
            return render_template(
                "batches/edit.html",
                batch=batch,
                error="Batch name is required."
            )

        if not academic_session:
            return render_template(
                "batches/edit.html",
                batch=batch,
                error="Academic session is required."
            )

        duplicate_batch = (
            Batch.query
            .filter(
                Batch.name == name,
                Batch.id != batch.id
            )
            .first()
        )

        if duplicate_batch:
            return render_template(
                "batches/edit.html",
                batch=batch,
                error=(
                    "Another batch already uses "
                    "this name."
                )
            )

        session_changed = (
            batch.academic_session
            != academic_session
        )

        batch.name = name
        batch.department = (
            department or None
        )
        batch.academic_session = (
            academic_session
        )

        if session_changed:

            courses = (
                Course.query
                .filter_by(batch_id=batch.id)
                .all()
            )

            for course in courses:

                course.academic_session = (
                    academic_session
                )

        db.session.commit()

        return redirect(
            url_for(
                "batches.list_batches"
            )
        )

    return render_template(
        "batches/edit.html",
        batch=batch
    )


# =========================================================
# BATCH STUDENTS
# =========================================================

@batches_bp.route(
    "/<int:batch_id>/students"
)
@login_required
def batch_students(batch_id):

    batch = db.session.get(
        Batch,
        batch_id
    )

    if not batch:
        return "Batch not found", 404

    students = (
        Student.query
        .filter_by(batch_id=batch.id)
        .order_by(Student.student_id.asc())
        .all()
    )

    return render_template(
        "students/batch_list.html",
        batch=batch,
        students=students
    )


# =========================================================
# IMPORT EXISTING STUDENTS
# =========================================================

@batches_bp.route(
    "/<int:batch_id>/import-students",
    methods=["GET", "POST"]
)
@login_required
def import_students(batch_id):

    batch = db.session.get(
        Batch,
        batch_id
    )

    if not batch:
        return "Batch not found", 404

    if not batch.is_active:
        return (
            "This batch is archived. "
            "Activate it before importing students.",
            400
        )

    # -----------------------------------------------------
    # GET
    # Show students currently not assigned to any batch.
    # -----------------------------------------------------

    if request.method == "GET":

        available_students = (
            Student.query
            .filter(Student.batch_id.is_(None))
            .order_by(Student.student_id.asc())
            .all()
        )

        return render_template(
            "batches/import_students.html",
            batch=batch,
            students=available_students
        )

    # -----------------------------------------------------
    # POST
    # Assign selected existing students to this batch.
    # -----------------------------------------------------

    selected_ids = request.form.getlist(
        "student_ids"
    )

    if not selected_ids:

        available_students = (
            Student.query
            .filter(Student.batch_id.is_(None))
            .order_by(Student.student_id.asc())
            .all()
        )

        return render_template(
            "batches/import_students.html",
            batch=batch,
            students=available_students,
            error="Please select at least one student."
        )

    imported_count = 0
    skipped_count = 0

    for student_id in selected_ids:

        if not student_id.isdigit():
            continue

        student = db.session.get(
            Student,
            int(student_id)
        )

        if not student:
            continue

        # Student is already assigned somewhere.
        if student.batch_id is not None:

            skipped_count += 1
            continue

        student.batch_id = batch.id

        imported_count += 1

    db.session.commit()

    return render_template(
        "batches/import_students_result.html",
        batch=batch,
        imported_count=imported_count,
        skipped_count=skipped_count
    )


# =========================================================
# ARCHIVE BATCH
# =========================================================

@batches_bp.route(
    "/<int:batch_id>/archive",
    methods=["POST"]
)
@login_required
def archive_batch(batch_id):

    batch = db.session.get(
        Batch,
        batch_id
    )

    if not batch:
        return "Batch not found", 404

    batch.is_active = False

    db.session.commit()

    return redirect(
        url_for(
            "batches.list_batches"
        )
    )


# =========================================================
# ACTIVATE BATCH
# =========================================================

@batches_bp.route(
    "/<int:batch_id>/activate",
    methods=["POST"]
)
@login_required
def activate_batch(batch_id):

    batch = db.session.get(
        Batch,
        batch_id
    )

    if not batch:
        return "Batch not found", 404

    batch.is_active = True

    db.session.commit()

    return redirect(
        url_for(
            "batches.list_batches"
        )
    )