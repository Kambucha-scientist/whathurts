from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from ..extensions import db
from ..models import User, EventLog
from ..forms import LoginForm

bp = Blueprint("auth", __name__)

def log_event(action, details="", user_id=None):
    db.session.add(EventLog(user_id=user_id if user_id is not None else (current_user.id if current_user.is_authenticated else None),
                            action=action, details=details))
    db.session.commit()

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        now = datetime.utcnow()
        if user and user.locked_until and user.locked_until > now:
            flash("Учетная запись временно заблокирована. Попробуйте позже.", "danger")
        elif user and user.is_active and user.check_password(form.password.data):
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
            login_user(user)
            log_event("login", "Успешный вход", user.id)
            return redirect(url_for("index"))
        else:
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = now + timedelta(minutes=5)
                    user.failed_login_attempts = 0
                db.session.commit()
            log_event("login_failed", f"Неудачный вход: {form.username.data}")
            flash("Неверный логин или пароль либо учетная запись отключена.", "danger")
    return render_template("login.html", form=form)

@bp.route("/logout")
@login_required
def logout():
    uid = current_user.id
    log_event("logout", "Выход из системы", uid)
    logout_user()
    flash("Вы вышли из системы.", "success")
    return redirect(url_for("auth.login"))
