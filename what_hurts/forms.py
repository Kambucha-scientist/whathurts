from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, DateTimeLocalField, BooleanField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from flask_wtf.file import FileField, FileAllowed
from .models import User

class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")

class PatientForm(FlaskForm):
    full_name = StringField("ФИО", validators=[DataRequired(), Length(max=160)])
    birth_date = DateField("Дата рождения", validators=[DataRequired()], format="%Y-%m-%d")
    phone = StringField("Телефон", validators=[DataRequired(), Length(max=40)])
    address = TextAreaField("Адрес", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Сохранить")

class MedicineForm(FlaskForm):
    name = StringField("Наименование", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Описание", validators=[Optional(), Length(max=3000)])
    characteristics = TextAreaField("Характеристики", validators=[Optional(), Length(max=3000)])
    side_effects = TextAreaField("Побочные эффекты", validators=[Optional(), Length(max=2000)])
    image_file = FileField("Изображение", validators=[
        Optional(),
        FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Только изображения (jpg, png, webp, gif)"),
    ])
    remove_image = BooleanField("Удалить текущее изображение")
    submit = SubmitField("Сохранить")

class CallForm(FlaskForm):
    patient_id = SelectField("Пациент", coerce=int, validators=[DataRequired()])
    datetime = DateTimeLocalField("Дата и время", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    complaints = TextAreaField("Жалобы", validators=[DataRequired(), Length(max=5000)])
    examination_results = TextAreaField("Результаты обследования", validators=[Optional(), Length(max=5000)])
    diagnosis = TextAreaField("Диагноз", validators=[DataRequired(), Length(max=3000)])
    recommendations = TextAreaField("Рекомендации", validators=[Optional(), Length(max=5000)])
    medicine_ids = SelectMultipleField("Лекарства", coerce=int, validators=[Optional()])
    submit = SubmitField("Сохранить")

class UserForm(FlaskForm):
    full_name = StringField("ФИО", validators=[DataRequired(), Length(max=160)])
    username = StringField("Логин", validators=[DataRequired(), Length(max=80)])
    role = SelectField("Роль", choices=[("doctor","Врач"),("analyst","Аналитик"),("admin","Администратор")], validators=[DataRequired()])
    is_active = BooleanField("Активен")
    password = PasswordField("Новый пароль", validators=[Optional(), Length(min=6, max=128)])
    submit = SubmitField("Сохранить")

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user and getattr(self, "_user_id", None) != user.id:
            raise ValidationError("Такой логин уже существует.")
