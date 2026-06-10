from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired


class VerifForm(FlaskForm):
    code = StringField('Введите код', validators=[DataRequired()])
    submit = SubmitField('Создать аккаунт')