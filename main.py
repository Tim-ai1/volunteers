from flask import Flask, redirect, render_template
import datetime
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_required, logout_user

from data import db_session
from data.tasks import Task
from data.users import User
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


@scheduler.task('interval', hours=1)
def archive_task():
    db_sess = db_session.create_session()
    expired_tasks = db_sess.query(Task).filter(Task.end_date <= datetime.datetime.now()).all()
    for task in expired_tasks:
        task.is_archived = True
        users = db_sess.query(User).filter(User.id == task.user.id).all()
        for user in users:
            user.current_tasks.remove(task.id)
            user.archived_tasks.append(task.id)


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
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='127.0.0.1', port=5001, debug=True)
