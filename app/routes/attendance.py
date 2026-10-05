from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)

from flask_login import (
    login_required,
    current_user
)

from app import db

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.attendance import (
    AttendanceSession,
    AttendanceRecord
)


attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/attendance"
)


# =========================================================
# TAKE ATTENDANCE
# =========================================================

@attendance_bp.route(
    "/course/<int:course_id>/take",
    methods=["GET", "POST"]
)
@login_required
def take_attendance(course_id):

    course = db.session.get(
        Course,
        course_id
    )

    if not course:
        return "Course not found", 404

    if course.teacher_id != current_user.id:
        return "Unauthorized", 403

    # -----------------------------------------------------
    # Get enrolled students
    # -----------------------------------------------------

    enrollments = (
        Enrollment.query
        .filter_by(
            course_id=course.id
        )
        .all()
    )

    students = sorted(
        [
            enrollment.student
            for enrollment in enrollments
        ],
        key=lambda student: student.student_id
    )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        date_string = request.form.get(
            "date",
            ""
        ).strip()

        weight = request.form.get(
            "attendance_weight",
            type=int
        )

        # -------------------------------------------------
        # Validate date
        # -------------------------------------------------

        if not date_string:

            return render_template(
                "attendance/take.html",
                course=course,
                students=students,
                error="Attendance date is required."
            )

        # -------------------------------------------------
        # Validate weight
        # -------------------------------------------------

        if not weight or weight < 1:

            return render_template(
                "attendance/take.html",
                course=course,
                students=students,
                error=(
                    "Attendance weight must be "
                    "at least 1."
                )
            )

        # -------------------------------------------------
        # Convert date
        # -------------------------------------------------

        try:

            attendance_date = datetime.strptime(
                date_string,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return render_template(
                "attendance/take.html",
                course=course,
                students=students,
                error="Invalid attendance date."
            )

        # -------------------------------------------------
        # Prevent duplicate attendance date
        # -------------------------------------------------

        existing_session = (
            AttendanceSession.query
            .filter_by(
                course_id=course.id,
                date=attendance_date
            )
            .first()
        )

        if existing_session:

            return render_template(
                "attendance/take.html",
                course=course,
                students=students,
                error=(
                    "Attendance has already been taken "
                    "for this date."
                )
            )

        # -------------------------------------------------
        # Create attendance session
        # -------------------------------------------------

        session = AttendanceSession(
            course_id=course.id,
            teacher_id=current_user.id,
            date=attendance_date,
            attendance_weight=weight
        )

        db.session.add(session)

        db.session.flush()

        # -------------------------------------------------
        # Create attendance records
        # -------------------------------------------------

        for student in students:

            status = request.form.get(
                f"student_{student.id}",
                "absent"
            )

            present = (
                status == "present"
            )

            record = AttendanceRecord(
                session_id=session.id,
                student_id=student.id,
                present=present
            )

            db.session.add(record)

        db.session.commit()

        return redirect(
            url_for(
                "attendance.attendance_history",
                course_id=course.id
            )
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "attendance/take.html",
        course=course,
        students=students
    )


# =========================================================
# ATTENDANCE HISTORY
# =========================================================

@attendance_bp.route(
    "/course/<int:course_id>/history"
)
@login_required
def attendance_history(course_id):

    course = db.session.get(
        Course,
        course_id
    )

    if not course:
        return "Course not found", 404

    if course.teacher_id != current_user.id:
        return "Unauthorized", 403

    # -----------------------------------------------------
    # Get enrolled students
    # -----------------------------------------------------

    enrollments = (
        Enrollment.query
        .filter_by(
            course_id=course.id
        )
        .all()
    )

    students = sorted(
        [
            enrollment.student
            for enrollment in enrollments
        ],
        key=lambda student: student.student_id
    )

    # -----------------------------------------------------
    # Get sessions
    # -----------------------------------------------------

    sessions = (
        AttendanceSession.query
        .filter_by(
            course_id=course.id
        )
        .order_by(
            AttendanceSession.date.asc(),
            AttendanceSession.id.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # Build attendance lookup
    # -----------------------------------------------------

    attendance_map = {
        student.id: {}
        for student in students
    }

    for session in sessions:

        for record in session.records:

            if record.student_id in attendance_map:

                attendance_map[
                    record.student_id
                ][session.id] = record

    # -----------------------------------------------------
    # Session statistics
    # -----------------------------------------------------

    session_stats = []

    for session in sessions:

        present_count = 0
        absent_count = 0

        for student in students:

            record = attendance_map[
                student.id
            ].get(session.id)

            if record:

                if record.present:
                    present_count += 1
                else:
                    absent_count += 1

        session_stats.append(
            {
                "session": session,
                "present": present_count,
                "absent": absent_count,
                "total": len(students)
            }
        )

    return render_template(
        "attendance/history.html",
        course=course,
        students=students,
        sessions=sessions,
        attendance_map=attendance_map,
        session_stats=session_stats
    )


# =========================================================
# EDIT ATTENDANCE SESSION
# =========================================================

@attendance_bp.route(
    "/session/<int:session_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_attendance(session_id):

    session = db.session.get(
        AttendanceSession,
        session_id
    )

    if not session:
        return "Attendance session not found", 404

    # -----------------------------------------------------
    # Authorization
    # -----------------------------------------------------

    if session.teacher_id != current_user.id:
        return "Unauthorized", 403

    course = session.course

    # -----------------------------------------------------
    # Get enrolled students
    # -----------------------------------------------------

    enrollments = (
        Enrollment.query
        .filter_by(
            course_id=course.id
        )
        .all()
    )

    students = sorted(
        [
            enrollment.student
            for enrollment in enrollments
        ],
        key=lambda student: student.student_id
    )

    # -----------------------------------------------------
    # Existing records
    # -----------------------------------------------------

    records = {
        record.student_id: record
        for record in session.records
    }

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    if request.method == "POST":

        date_string = request.form.get(
            "date",
            ""
        ).strip()

        weight = request.form.get(
            "attendance_weight",
            type=int
        )

        # -------------------------------------------------
        # Validate
        # -------------------------------------------------

        if not date_string:

            return render_template(
                "attendance/edit.html",
                course=course,
                session=session,
                students=students,
                records=records,
                error="Attendance date is required."
            )

        if not weight or weight < 1:

            return render_template(
                "attendance/edit.html",
                course=course,
                session=session,
                students=students,
                records=records,
                error=(
                    "Attendance weight must be "
                    "at least 1."
                )
            )

        # -------------------------------------------------
        # Convert date
        # -------------------------------------------------

        try:

            new_date = datetime.strptime(
                date_string,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return render_template(
                "attendance/edit.html",
                course=course,
                session=session,
                students=students,
                records=records,
                error="Invalid attendance date."
            )

        # -------------------------------------------------
        # Check duplicate date
        # -------------------------------------------------

        duplicate_session = (
            AttendanceSession.query
            .filter(
                AttendanceSession.course_id == course.id,
                AttendanceSession.date == new_date,
                AttendanceSession.id != session.id
            )
            .first()
        )

        if duplicate_session:

            return render_template(
                "attendance/edit.html",
                course=course,
                session=session,
                students=students,
                records=records,
                error=(
                    "Another attendance session already "
                    "exists for this date."
                )
            )

        # -------------------------------------------------
        # Update session
        # -------------------------------------------------

        session.date = new_date
        session.attendance_weight = weight

        # -------------------------------------------------
        # Update each student's attendance
        # -------------------------------------------------

        for student in students:

            status = request.form.get(
                f"student_{student.id}",
                "absent"
            )

            present = (
                status == "present"
            )

            record = records.get(
                student.id
            )

            if record:

                record.present = present

            else:

                record = AttendanceRecord(
                    session_id=session.id,
                    student_id=student.id,
                    present=present
                )

                db.session.add(record)

        db.session.commit()

        return redirect(
            url_for(
                "attendance.attendance_history",
                course_id=course.id
            )
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    return render_template(
        "attendance/edit.html",
        course=course,
        session=session,
        students=students,
        records=records
    )


# =========================================================
# DELETE ATTENDANCE SESSION
# =========================================================

@attendance_bp.route(
    "/session/<int:session_id>/delete",
    methods=["POST"]
)
@login_required
def delete_attendance(session_id):

    session = db.session.get(
        AttendanceSession,
        session_id
    )

    if not session:
        return "Attendance session not found", 404

    if session.teacher_id != current_user.id:
        return "Unauthorized", 403

    course_id = session.course_id

    # Attendance records are automatically deleted because
    # AttendanceSession uses cascade="all, delete-orphan".

    db.session.delete(session)

    db.session.commit()

    return redirect(
        url_for(
            "attendance.attendance_history",
            course_id=course_id
        )
    )