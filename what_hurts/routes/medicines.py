from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Medicine, EventLog
from ..forms import MedicineForm
from ..decorators import role_required
from ..utils import save_medicine_image, delete_medicine_image

bp = Blueprint("medicines", __name__, url_prefix="/medicines")


@bp.route("/")
@login_required
def list_medicines():
    return render_template(
        "medicines/list.html",
        medicines=Medicine.query.order_by(Medicine.name).all(),
    )


@bp.route("/create", methods=["GET", "POST"])
@role_required("doctor", "admin")
def create_medicine():
    form = MedicineForm()
    if form.validate_on_submit():
        try:
            filename = save_medicine_image(form.image_file.data)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("medicines/form.html", form=form, title="Новое лекарство")

        m = Medicine(
            name=form.name.data,
            description=form.description.data or "",
            characteristics=form.characteristics.data or "",
            side_effects=form.side_effects.data or "",
            image_filename=filename or "",
        )
        db.session.add(m)
        db.session.flush()
        db.session.add(EventLog(
            user_id=current_user.id,
            action="medicine_add",
            details=f"Добавлено лекарство {m.name}",
        ))
        db.session.commit()
        flash("Лекарство добавлено.", "success")
        return redirect(url_for("medicines.list_medicines"))

    return render_template("medicines/form.html", form=form, title="Новое лекарство")


@bp.route("/edit/<int:medicine_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_medicine(medicine_id):
    m = Medicine.query.get_or_404(medicine_id)
    form = MedicineForm(obj=m)
    if form.validate_on_submit():
        m.name = form.name.data
        m.description = form.description.data or ""
        m.characteristics = form.characteristics.data or ""
        m.side_effects = form.side_effects.data or ""

        if form.remove_image.data:
            delete_medicine_image(m.image_filename)
            m.image_filename = ""

        try:
            new_filename = save_medicine_image(form.image_file.data)
        except ValueError as e:
            flash(str(e), "danger")
            return render_template(
                "medicines/form.html", form=form, title="Редактирование лекарства", medicine=m
            )

        if new_filename:
            delete_medicine_image(m.image_filename)
            m.image_filename = new_filename

        db.session.commit()
        flash("Лекарство обновлено.", "success")
        return redirect(url_for("medicines.list_medicines"))

    return render_template(
        "medicines/form.html", form=form, title="Редактирование лекарства", medicine=m
    )


@bp.route("/delete/<int:medicine_id>", methods=["POST"])
@role_required("admin")
def delete_medicine(medicine_id):
    m = Medicine.query.get_or_404(medicine_id)

    for c in list(m.calls):
        c.medicines.remove(m)

    filename = m.image_filename
    db.session.delete(m)
    db.session.commit()
    delete_medicine_image(filename)

    flash("Лекарство удалено.", "success")
    return redirect(url_for("medicines.list_medicines"))