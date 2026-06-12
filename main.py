from flask import Flask, redirect, request, url_for, render_template, session
import datetime
from email.utils import parsedate_to_datetime
import random
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_required, logout_user, login_user, current_user

from data import db_session
from data.tasks import Task
from data.users import User
from data.user_task import UserTask
from forms.login import LoginForm
from forms.org_registration import OrgRegisterForm
from forms.user_registration import UserRegisterForm
from forms.verification import VerifForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-123456789'
login_manager = LoginManager()
login_manager.init_app(app)
scheduler = APScheduler()

db_session.global_init("db/web-volunteers.db")

# import sqlite3
# with sqlite3.connect("db/web-volunteers.db") as conn:
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO roles (id, title) VALUES (1, 'Волонтёр'), (2, 'Организация')")
#     conn.commit()
#
# код для заполнения таблицы roles (запускается один раз)


@scheduler.task('interval', minutes=30)
def archive_task():
    db_sess = db_session.create_session()
    expired_tasks = db_sess.query(Task).filter(Task.end_date <= datetime.datetime.now()).all()
    for task in expired_tasks:
        task.is_archived = True


def check_form(form):
    db_sess = db_session.create_session()
    if form.password.data != form.password_again.data:
        return 'Пароли не совпадают'
    elif db_sess.query(User).filter(User.email == form.email.data).first():
        return 'Аккаунт с этой почтой уже существует'
    elif db_sess.query(User).filter(User.phone_number == form.phone_number.data).first():
        return 'Аккаунт с этим номером телефона уже существует'
    elif db_sess.query(User).filter(User.name == form.name.data).first():
        return 'Аккаунт с таким именем уже существует'
    return None


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def index():
    return 'index'


@app.route('/register', methods=['GET', 'POST'])
def register():
    state = request.args.get('state')
    if state == 'volunteer':
        form = UserRegisterForm()
        if form.validate_on_submit():
            error = check_form(form)
            if error:
                return render_template('test.html', form=form)
            user_data = {
                'name':form.name.data,
                'email':form.email.data,
                'phone_number':form.phone_number.data,
                'birth_date':form.birth_date.data,
                'info':form.info.data,
                 'role_id':1,
                'password': form.password.data
            }
            session['user_data'] = user_data
            code = str(random.randint(0, 999999))
            code = '0' * (6 - len(code)) + code
            session['code'] = code
            return redirect("/verification")
        return render_template('test.html', form=form)
    elif state == 'organization':
        form = OrgRegisterForm()
        if form.validate_on_submit():
            error = check_form(form)
            if error:
                return render_template('test.html', form=form)
            user_data = {
                'name': form.name.data,
                'email': form.email.data,
                'phone_number': form.phone_number.data,
                'info': form.info.data,
                'address': form.address.data,
                'role_id': 2,
                'password': form.password.data
            }
            session['user_data'] = user_data
            code = str(random.randint(0, 999999))
            code = '0' * (6 - len(code)) + code
            session['code'] = code
            return redirect("/verification")
        return render_template('test.html', form=form)


@app.route('/verification', methods=['GET', 'POST'])
def verification():
    user_data = session.get('user_data')
    code = session.get('code')
    print(code) # потом будет отправка на почту
    form = VerifForm()
    if request.method == 'GET':
        return render_template('test2.html', form=form)
    if form.validate_on_submit():
        if form.code.data == code:
            user = User(
                name=user_data['name'],
                email=user_data['email'],
                phone_number=user_data['phone_number'],
                info=user_data['info'],
                role_id=user_data['role_id']
            )
            user.set_password(user_data['password'])
            if 'address' in user_data:
                user.address = user_data['address']
            if 'birth_date' in user_data:
                dt = parsedate_to_datetime(user_data['birth_date'])
                user.birth_date = dt.date()
            db_sess = db_session.create_session()
            db_sess.add(user)
            db_sess.commit()
            return redirect('/')
        return 'нет'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return 'вы авторизованы'
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', form=form, error='Неверный логин/пароль')
    return render_template('login.html', form=form)


@app.route('/tasks')
def tasks():
    db_sess = db_session.create_session()
    tasks = db_sess.query(Task).filter(Task.is_archived == False).all()
    return render_template('tasks.html', tasks=tasks)


@app.route('/task/<int:task_id>')
def task(task_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == task_id).first()
    return render_template('task.html', task=task, role_id=current_user.role_id)


@app.route('/take_part/<int:task_id>')
def take_part(task_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == task_id).first()
    if current_user.role_id != 1 or task.is_archived == True:
        return 'отказано'
    user_task = db_sess.query(UserTask).filter(UserTask.task_id == task_id,
                                               UserTask.user_id == current_user.id).first()
    if user_task:
        return 'вы уже зарегистрированы на это событие'
    user_task = UserTask(
        user_id=current_user.id,
        task_id=task_id
    )
    db_sess.add(user_task)
    db_sess.commit()
    return 'готово'


@app.route('/task/<int:id>', methods=['GET', 'POST'])
def taskid(id):
    return render_template('task.html', task=task)


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run()
