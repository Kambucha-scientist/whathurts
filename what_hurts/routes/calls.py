from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from ..extensions import db
from ..models import Call, Patient, Medicine, EventLog, User
from ..forms import CallForm
from ..decorators import role_required

bp = Blueprint("calls", __name__, url_prefix="/calls")

def prepare_form(form):
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.full_name).all()]
    form.medicine_ids.choices = [(m.id, m.name) for m in Medicine.query.order_by(Medicine.name).all()]

def save_log(action, details):
    db.session.add(EventLog(user_id=current_user.id, action=action, details=details))
    db.session.commit()

@bp.route("/")
@role_required("analyst", "admin")
def list_calls():
    q = Call.query
    start = request.args.get("start_date"); end = request.args.get("end_date")
    doctor_id = request.args.get("doctor_id", type=int); patient_id = request.args.get("patient_id", type=int)
    if start:
        try: q = q.filter(Call.datetime >= datetime.strptime(start, "%Y-%m-%d"))
        except ValueError: flash("Некорректная дата начала.", "warning")
    if end:
        try: q = q.filter(Call.datetime < datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59))
        except ValueError: flash("Некорректная дата окончания.", "warning")
    if doctor_id: q = q.filter_by(doctor_id=doctor_id)
    if patient_id: q = q.filter_by(patient_id=patient_id)
    calls = q.order_by(Call.datetime.desc()).all()
    return render_template("calls/list.html", calls=calls, doctors=User.query.filter_by(role="doctor").all(),
                           patients=Patient.query.all(), filters=request.args)

@bp.route("/my")
@role_required("doctor")
def my_calls():
    calls = Call.query.filter_by(doctor_id=current_user.id).order_by(Call.datetime.desc()).all()
    return render_template("calls/my.html", calls=calls)

@bp.route("/create", methods=["GET", "POST"])
@role_required("doctor")
def create_call():
    form = CallForm(); prepare_form(form)
    if request.method == "GET": form.datetime.data = datetime.now()
    if form.validate_on_submit():
        call = Call(patient_id=form.patient_id.data, doctor_id=current_user.id, datetime=form.datetime.data,
                    complaints=form.complaints.data, examination_results=form.examination_results.data,
                    diagnosis=form.diagnosis.data, recommendations=form.recommendations.data,
                    medicines=Medicine.query.filter(Medicine.id.in_(form.medicine_ids.data)).all())
        db.session.add(call); db.session.commit()
        save_log("call_create", f"Создан вызов #{call.id}")
        flash("Вызов создан.", "success")
        return redirect(url_for("calls.call_detail", call_id=call.id))
    return render_template("calls/form.html", form=form, title="Новый вызов")

@bp.route("/<int:call_id>")
@login_required
def call_detail(call_id):
    call = Call.query.get_or_404(call_id)
    if current_user.role == "doctor" and call.doctor_id != current_user.id:
        from flask import abort
        abort(403)
    return render_template("calls/detail.html", call=call)

@bp.route("/<int:call_id>/edit", methods=["GET", "POST"])
@role_required("doctor")
def edit_call(call_id):
    call = Call.query.get_or_404(call_id)
    if call.doctor_id != current_user.id:
        from flask import abort
        abort(403)
    form = CallForm(obj=call); prepare_form(form)
    if request.method == "GET": form.medicine_ids.data = [m.id for m in call.medicines]
    if form.validate_on_submit():
        call.patient_id=form.patient_id.data; call.datetime=form.datetime.data
        call.complaints=form.complaints.data; call.examination_results=form.examination_results.data
        call.diagnosis=form.diagnosis.data; call.recommendations=form.recommendations.data
        call.medicines=Medicine.query.filter(Medicine.id.in_(form.medicine_ids.data)).all()
        db.session.commit(); save_log("call_edit", f"Изменен вызов #{call.id}")
        flash("Вызов обновлен.", "success")
        return redirect(url_for("calls.call_detail", call_id=call.id))
    return render_template("calls/form.html", form=form, title="Редактирование вызова")
