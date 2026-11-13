from flask import Blueprint, render_template, redirect, url_for, flash
from ..extensions import db
from ..models import User, EventLog
from ..forms import UserForm
from ..decorators import role_required

bp=Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/users")
@role_required("admin")
def users():
    return render_template("admin/users.html", users=User.query.order_by(User.full_name).all())

@bp.route("/users/create", methods=["GET","POST"])
@role_required("admin")
def create_user():
    form=UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Логин уже занят.","danger")
        elif not form.password.data or len(form.password.data)<6:
            flash("Для нового пользователя задайте пароль не короче 6 символов.","danger")
        else:
            u=User(username=form.username.data,full_name=form.full_name.data,role=form.role.data,is_active=form.is_active.data)
            u.set_password(form.password.data); db.session.add(u); db.session.flush()
            db.session.add(EventLog(user_id=None,action="user_create",details=f"Создан пользователь {u.username}"))
            db.session.commit(); flash("Пользователь создан.","success")
            return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html",form=form,title="Новый пользователь")

@bp.route("/users/<int:user_id>/edit", methods=["GET","POST"])
@role_required("admin")
def edit_user(user_id):
    u=User.query.get_or_404(user_id); form=UserForm(obj=u); form._user_id=u.id
    if form.validate_on_submit():
        u.full_name=form.full_name.data; u.username=form.username.data; u.role=form.role.data; u.is_active=form.is_active.data
        if form.password.data: u.set_password(form.password.data)
        db.session.add(EventLog(action="user_edit",details=f"Изменен пользователь {u.username}"))
        db.session.commit(); flash("Пользователь обновлен.","success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_form.html",form=form,title="Редактирование пользователя")

@bp.route("/events")
@role_required("admin")
def events():
    return render_template("admin/events.html", events=EventLog.query.order_by(EventLog.timestamp.desc()).limit(100).all())
