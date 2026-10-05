from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.models.course import Course
from app.models.batch import Batch
from app.models.student import Student
from app.models.enrollment import Enrollment
from app.models.attendance import AttendanceSession


courses_bp = Blueprint(
    "courses",
    __name__,
    url_prefix="/courses"
)


def get_teacher_course(course_id):
    course = db.session.get(Course, course_id)

    if not course:
        return None

    if course.teacher_id != current_user.id:
        return None

    return course


def get_course_academic_session(course):
    """
    Batch is the source of truth for academic session.
    """

    if course.batch:
        return course.batch.academic_session

    return course.academic_session


@courses_bp.route("/")
@login_required
def list_courses():

    courses = (
        Course.query
        .filter_by(teacher_id=current_user.id)
        .all()
    )

    courses.sort(
        key=lambda course: (
            (course.course_code or "").upper(),
            (
                course.batch.name.upper()
                if course.batch
                else ""
            ),
            (
                get_course_academic_session(course)
                or ""
            )
        )
    )

    return render_template(
        "courses/list.html",
        courses=courses
    )


@courses_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_course():

    batches = (
        Batch.query
        .filter_by(is_active=True)
        .order_by(Batch.name.asc())
        .all()
    )

    if request.method == "POST":

        course_code = (
            request.form.get(
                "course_code",
                ""
            )
            .strip()
            .upper()
        )

        course_name = (
            request.form.get(
                "course_name",
                ""
            )
            .strip()
        )

        batch_id = request.form.get(
            "batch_id",
            type=int
        )

        if not course_code:
            return render_template(
                "courses/add.html",
                batches=batches,
                error="Course code is required."
            )

        if not course_name:
            return render_template(
                "courses/add.html",
                batches=batches,
                error="Course name is required."
            )

        if not batch_id:
            return render_template(
                "courses/add.html",
                batches=batches,
                error="Please select a batch."
            )

        batch = db.session.get(
            Batch,
            batch_id
        )

        if not batch:
            return render_template(
                "courses/add.html",
                batches=batches,
                error="Selected batch does not exist."
            )

        if not batch.is_active:
            return render_template(
                "courses/add.html",
                batches=batches,
                error=(
                    "This batch is archived. "
                    "Activate it before creating "
                    "a new course."
                )
            )

        course = Course(
            course_code=course_code,
            course_name=course_name,
            teacher_id=current_user.id,
            batch_id=batch.id,

            # Store a synchronized copy.
            academic_session=batch.academic_session
        )

        db.session.add(course)
        db.session.commit()

        return redirect(
            url_for(
                "courses.course_details",
                course_id=course.id
            )
        )

    return render_template(
        "courses/add.html",
        batches=batches
    )


@courses_bp.route("/<int:course_id>")
@login_required
def course_details(course_id):

    course = get_teacher_course(course_id)

    if not course:
        return "Course not found or unauthorized", 404

    enrollments = (
        Enrollment.query
        .filter_by(course_id=course.id)
        .all()
    )

    enrolled_students = sorted(
        [
            enrollment.student
            for enrollment in enrollments
        ],
        key=lambda student: student.student_id
    )

    enrolled_ids = {
        student.id
        for student in enrolled_students
    }

    if course.batch_id:

        query = Student.query.filter(
            Student.batch_id == course.batch_id
        )

        if enrolled_ids:
            query = query.filter(
                ~Student.id.in_(enrolled_ids)
            )

        available_students = (
            query
            .order_by(Student.student_id.asc())
            .all()
        )

    else:
        available_students = []

    attendance_count = (
        AttendanceSession.query
        .filter_by(course_id=course.id)
        .count()
    )

    academic_session = get_course_academic_session(
        course
    )

    return render_template(
        "courses/details.html",
        course=course,
        enrolled_students=enrolled_students,
        available_students=available_students,
        attendance_count=attendance_count,
        academic_session=academic_session
    )


@courses_bp.route(
    "/<int:course_id>/enroll-batch",
    methods=["POST"]
)
@login_required
def enroll_batch(course_id):

    course = get_teacher_course(course_id)

    if not course:
        return "Course not found or unauthorized", 404

    if not course.batch_id:
        return (
            "This course does not have a batch assigned.",
            400
        )

    batch_students = (
        Student.query
        .filter_by(batch_id=course.batch_id)
        .order_by(Student.student_id.asc())
        .all()
    )

    existing_enrollments = (
        Enrollment.query
        .filter_by(course_id=course.id)
        .all()
    )

    existing_student_ids = {
        enrollment.student_id
        for enrollment in existing_enrollments
    }

    selected_ids = request.form.getlist(
        "student_ids"
    )

    if selected_ids:

        selected_ids = {
            int(student_id)
            for student_id in selected_ids
            if student_id.isdigit()
        }

        students_to_import = [
            student
            for student in batch_students
            if student.id in selected_ids
        ]

    else:
        students_to_import = batch_students

    for student in students_to_import:

        if student.batch_id != course.batch_id:
            continue

        if student.id in existing_student_ids:
            continue

        enrollment = Enrollment(
            student_id=student.id,
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


@courses_bp.route(
    "/<int:course_id>/remove-student/<int:student_id>",
    methods=["POST"]
)
@login_required
def remove_student(course_id, student_id):

    course = get_teacher_course(course_id)

    if not course:
        return "Course not found or unauthorized", 404

    enrollment = (
        Enrollment.query
        .filter_by(
            course_id=course.id,
            student_id=student_id
        )
        .first()
    )

    if not enrollment:
        return (
            "Student is not enrolled in this course.",
            404
        )

    db.session.delete(enrollment)
    db.session.commit()

    return redirect(
        url_for(
            "courses.course_details",
            course_id=course.id
        )
    )


@courses_bp.route(
    "/<int:course_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_course(course_id):

    course = get_teacher_course(course_id)

    if not course:
        return "Course not found or unauthorized", 404

    batches = (
        Batch.query
        .order_by(Batch.name.asc())
        .all()
    )

    enrollment_count = (
        Enrollment.query
        .filter_by(course_id=course.id)
        .count()
    )

    has_students = enrollment_count > 0

    if request.method == "POST":

        course_code = (
            request.form.get(
                "course_code",
                ""
            )
            .strip()
            .upper()
        )

        course_name = (
            request.form.get(
                "course_name",
                ""
            )
            .strip()
        )

        batch_id = request.form.get(
            "batch_id",
            type=int
        )

        if not course_code:
            return render_template(
                "courses/edit.html",
                course=course,
                batches=batches,
                has_students=has_students,
                error="Course code is required."
            )

        if not course_name:
            return render_template(
                "courses/edit.html",
                course=course,
                batches=batches,
                has_students=has_students,
                error="Course name is required."
            )

        if has_students:

            batch_id = course.batch_id

        else:

            if not batch_id:
                return render_template(
                    "courses/edit.html",
                    course=course,
                    batches=batches,
                    has_students=has_students,
                    error="Please select a batch."
                )

        batch = db.session.get(
            Batch,
            batch_id
        )

        if not batch:
            return render_template(
                "courses/edit.html",
                course=course,
                batches=batches,
                has_students=has_students,
                error="Selected batch does not exist."
            )

        if (
            not batch.is_active
            and batch.id != course.batch_id
        ):
            return render_template(
                "courses/edit.html",
                course=course,
                batches=batches,
                has_students=has_students,
                error=(
                    "You cannot move a course "
                    "to an archived batch."
                )
            )

        course.course_code = course_code
        course.course_name = course_name
        course.batch_id = batch.id

        # Keep Course's stored copy synchronized
        # with the Batch.
        course.academic_session = (
            batch.academic_session
        )

        db.session.commit()

        return redirect(
            url_for(
                "courses.course_details",
                course_id=course.id
            )
        )

    return render_template(
        "courses/edit.html",
        course=course,
        batches=batches,
        has_students=has_students
    )


@courses_bp.route(
    "/<int:course_id>/delete",
    methods=["POST"]
)
@login_required
def delete_course(course_id):

    course = get_teacher_course(course_id)

    if not course:
        return "Course not found or unauthorized", 404

    attendance_sessions = (
        AttendanceSession.query
        .filter_by(course_id=course.id)
        .all()
    )

    for session in attendance_sessions:
        db.session.delete(session)

    Enrollment.query.filter_by(
        course_id=course.id
    ).delete()

    db.session.delete(course)

    db.session.commit()

    return redirect(
        url_for(
            "courses.list_courses"
        )
    )