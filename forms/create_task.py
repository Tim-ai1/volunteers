from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, MultipleFileField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

class CreateTaskForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    info = TextAreaField('Описание', validators=[DataRequired()])
    files = MultipleFileField('Добавить фото (опционально)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Только изображения (.jpg, .png)')
    ])
    start_date = DateField('Дата начала', validators=[DataRequired()])
    end_date = DateField('Дата конца', validators=[DataRequired()])
    address = StringField('Адрес', validators=[DataRequired()])
    people_count = IntegerField('Количество волонтёров', validators=[DataRequired()])
    tags = StringField('Теги', validators=[DataRequired()])
    submit = SubmitField('Создать')