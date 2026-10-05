from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user

from app.models.teacher import Teacher


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        teacher = Teacher.query.filter_by(
            email=email
        ).first()

        if teacher and teacher.check_password(password):
            login_user(teacher)

            return redirect(
                url_for("dashboard.dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    logout_user()

    return redirect(
        url_for("auth.login")
    )