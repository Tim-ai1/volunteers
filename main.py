from flask import Flask, redirect, render_template
import datetime
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_required, logout_user, login_user, current_user

from data import db_session
from data.tasks import Task
from data.users import User
from data.user_task import UserTask
from forms.login import LoginForm
from forms.org_registration import OrgRegisterForm
from forms.user_registration import UserRegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = ''
login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/web-volunteers.db")

# import sqlite3
# with sqlite3.connect("db/web-volunteers.db") as conn:
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO roles (id, title) VALUES (1, 'Волонтёр'), (2, 'Организация')")
#     conn.commit()
#
# код для заполнения таблицы roles (запускается один раз)

app = Flask(__name__)
scheduler = APScheduler()

@scheduler.task('interval', minutes=30)
def archive_task():
    db_sess = db_session.create_session()
    expired_tasks = db_sess.query(Task).filter(Task.end_date <= datetime.datetime.now()).all()
    for task in expired_tasks:
        task.is_archived = True


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')


@app.route('/')
def base():
    return render_template('base.html')


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


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='127.0.0.1', port=5001, debug=True)
