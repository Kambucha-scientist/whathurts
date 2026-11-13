from flask import Flask, render_template
from .config import Config
from .extensions import db, login_manager, csrf

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .routes.auth import bp as auth_bp
    from .routes.patients import bp as patients_bp
    from .routes.calls import bp as calls_bp
    from .routes.medicines import bp as medicines_bp
    from .routes.reports import bp as reports_bp
    from .routes.admin import bp as admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(calls_bp)
    app.register_blueprint(medicines_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        from flask_login import current_user
        from flask import redirect, url_for
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        return render_template("index.html")

    @app.errorhandler(403)
    def forbidden(error): return render_template("errors/403.html"), 403
    @app.errorhandler(404)
    def not_found(error): return render_template("errors/404.html"), 404
    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
