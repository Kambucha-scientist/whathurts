import csv
from io import StringIO
from datetime import datetime
from flask import Blueprint, render_template, request, Response, flash
from ..models import Call, User
from ..decorators import role_required

bp = Blueprint("reports", __name__, url_prefix="/reports")


def _normalize_disease(value: str) -> str:
    """Пустой диагноз сводим к понятной метке, чтобы он не терялся в отчёте."""
    value = (value or "").strip()
    return value if value else "Не указан"


def _filter_args_without(*keys):
    """GET-параметры, очищенные от указанных ключей — чтобы url_for не дублировал их."""
    args = request.args.to_dict(flat=True)
    for k in keys:
        args.pop(k, None)
    return args


def filtered_calls():
    q = Call.query
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    if start:
        try:
            q = q.filter(Call.datetime >= datetime.strptime(start, "%Y-%m-%d"))
        except ValueError:
            flash("Некорректная дата начала.", "warning")
    if end:
        try:
            q = q.filter(
                Call.datetime
                <= datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            )
        except ValueError:
            flash("Некорректная дата окончания.", "warning")
    return q.order_by(Call.datetime.desc())


def _disease_stats():
    """Группирует вызовы по диагнозу: уникальные пациенты + количество вызовов."""
    calls = filtered_calls().all()
    stats = {}
    for c in calls:
        disease = _normalize_disease(c.diagnosis)
        entry = stats.setdefault(disease, {"patients": set(), "calls": 0})
        entry["patients"].add(c.patient_id)
        entry["calls"] += 1
    rows = [
        {"disease": d, "patient_count": len(v["patients"]), "call_count": v["calls"]}
        for d, v in stats.items()
    ]
    rows.sort(key=lambda r: (-r["patient_count"], r["disease"]))
    return rows


@bp.route("/")
@role_required("analyst", "admin")
def index():
    calls = filtered_calls().all()
    return render_template(
        "reports/index.html",
        calls=calls,
        doctors=User.query.filter_by(role="doctor").all(),
        filter_args=_filter_args_without("disease"),
    )


@bp.route("/summary")
@role_required("analyst", "admin")
def summary():
    calls = filtered_calls().all()
    totals = {}
    for c in calls:
        totals[c.doctor.full_name] = totals.get(c.doctor.full_name, 0) + 1
    return render_template(
        "reports/summary.html",
        totals=totals,
        filter_args=_filter_args_without("disease"),
    )


@bp.route("/by-disease")
@role_required("analyst", "admin")
def by_disease():
    rows = _disease_stats()
    calls = filtered_calls().all()
    return render_template(
        "reports/disease.html",
        rows=rows,
        total_patients=len({c.patient_id for c in calls}),
        total_calls=len(calls),
        filter_args=_filter_args_without("disease"),
    )


@bp.route("/by-disease/<disease>")
@role_required("analyst", "admin")
def disease_detail(disease):
    calls = [c for c in filtered_calls().all() if _normalize_disease(c.diagnosis) == disease]
    patients = {c.patient_id: c.patient for c in calls}
    return render_template(
        "reports/disease_detail.html",
        disease=disease,
        patients=list(patients.values()),
        calls=calls,
        filter_args=_filter_args_without("disease"),
    )


@bp.route("/by-disease.csv")
@role_required("analyst", "admin")
def by_disease_csv():
    rows = _disease_stats()
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Болезнь (диагноз)", "Количество больных", "Количество вызовов"])
    for r in rows:
        writer.writerow([r["disease"], r["patient_count"], r["call_count"]])
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=diseases.csv"},
    )



@bp.route("/export.csv")
@role_required("analyst", "admin")
def export_csv():
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Дата", "Врач", "Пациент", "Диагноз"])
    for c in filtered_calls().all():
        writer.writerow([
            c.datetime.strftime("%d.%m.%Y %H:%M"),
            c.doctor.full_name,
            c.patient.full_name,
            c.diagnosis,
        ])
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=report.csv"},
    )