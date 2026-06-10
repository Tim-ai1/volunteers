from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField, StringField
from wtforms.fields.datetime import DateField
from wtforms.fields.simple import TelField
from wtforms.validators import DataRequired


class UserRegisterForm(FlaskForm):
    email = EmailField('Адрес электронной почты', validators=[DataRequired()])
    phone_number = TelField('Номер телефона', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    birth_date = DateField('Дата рождения', format='%Y-%m-%d', validators=[DataRequired()])
    info = StringField('О себе')
    submit = SubmitField('Продолжить')
