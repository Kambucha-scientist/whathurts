from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

call_medicines = db.Table(
    "call_medicines",
    db.Column("call_id", db.Integer, db.ForeignKey("call.id"), primary_key=True),
    db.Column("medicine_id", db.Integer, db.ForeignKey("medicine.id"), primary_key=True),
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime)
    calls = db.relationship("Call", back_populates="doctor")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(160), nullable=False, index=True)
    birth_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), nullable=False)
    calls = db.relationship("Call", back_populates="patient", cascade="all, delete-orphan")

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, unique=True)
    description = db.Column(db.Text, default="")
    characteristics = db.Column(db.Text, default="")
    side_effects = db.Column(db.Text, default="")        
    image_filename = db.Column(db.String(255), default="")

    calls = db.relationship(
        "Call",
        secondary=call_medicines,
        back_populates="medicines",
        lazy="select",
    )    

class Call(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, default=lambda: datetime.utcnow())
    complaints = db.Column(db.Text, nullable=False)
    examination_results = db.Column(db.Text, default="")
    diagnosis = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow(), nullable=False)
    patient = db.relationship("Patient", back_populates="calls")
    doctor = db.relationship("User", back_populates="calls")
    medicines = db.relationship("Medicine", secondary=call_medicines, back_populates="calls", lazy="select")

class EventLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.utcnow(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(40), nullable=False)
    details = db.Column(db.Text, default="")
    user = db.relationship("User")
