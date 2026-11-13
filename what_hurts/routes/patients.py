from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from ..extensions import db
from ..models import Patient
from ..forms import PatientForm
from ..decorators import role_required

bp = Blueprint("patients", __name__, url_prefix="/patients")

@bp.route("/")
@login_required
def list_patients():
    patients = Patient.query.order_by(Patient.full_name).all()
    return render_template("patients/list.html", patients=patients)

@bp.route("/create", methods=["GET", "POST"])
@role_required("doctor", "admin")
def create_patient():
    form = PatientForm()
    if form.validate_on_submit():
        p = Patient(full_name=form.full_name.data, birth_date=form.birth_date.data,
                    phone=form.phone.data, address=form.address.data)
        db.session.add(p); db.session.commit()
        flash("Пациент создан.", "success")
        return redirect(url_for("patients.list_patients"))
    return render_template("patients/form.html", form=form, title="Новый пациент")

@bp.route("/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("patients/detail.html", patient=patient)

@bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@role_required("doctor", "admin")
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient); db.session.commit()
        flash("Данные пациента обновлены.", "success")
        return redirect(url_for("patients.patient_detail", patient_id=patient.id))
    return render_template("patients/form.html", form=form, title="Редактирование пациента")
