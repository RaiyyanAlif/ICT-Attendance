from flask import Flask
from flask_mail import Mail
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Initialize login manager
    login_manager.init_app(app)

    mail.init_app(app)

    login_manager.login_view = "auth.login"

    @app.route("/db-test")
    def db_test():
        try:
            db.session.execute(db.text("SELECT 1"))
            return "Database connection successful! ✅"
        except Exception as e:
            return f"Database connection failed: {e}"

    # Create database tables
    with app.app_context():
        from app import models
        db.create_all()

    # Load logged-in teacher
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.teacher import Teacher

        return db.session.get(
            Teacher,
            int(user_id)
        )

    # Register routes
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.batches import batches_bp
    from app.routes.students import students_bp
    from app.routes.courses import courses_bp
    from app.routes.attendance import attendance_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(batches_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)


    return app