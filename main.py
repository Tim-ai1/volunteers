from flask import Flask, redirect, request, url_for, render_template, session, jsonify
import datetime
from email.utils import parsedate_to_datetime
import random
import os
from werkzeug.utils import secure_filename
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_required, logout_user, login_user, current_user

from data import db_session
from data.tasks import Task
from data.users import User
from data.user_task import UserTask
from forms.admin_login import AdminLoginForm
from forms.login import LoginForm
from forms.org_registration import OrgRegisterForm
from forms.volunteer_registration import VolunteerRegisterForm
from forms.verification import VerifForm
from forms.create_task import CreateTaskForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-123456789'
app.config['UPLOAD_FOLDER'] = 'static/upload'
login_manager = LoginManager()
login_manager.init_app(app)
scheduler = APScheduler()

db_session.global_init("db/web-volunteers.db")

# import sqlite3
# with sqlite3.connect("db/web-volunteers.db") as conn:
#     cursor = conn.cursor()
    # cursor.execute("INSERT INTO roles (id, title) VALUES (1, 'Волонтёр'), (2, 'Организация')")
    # cursor.execute("INSERT INTO roles (id, title) VALUES (3, 'Админ')")
    # conn.commit()
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


def is_admin(user):
    return user.role_id == 3


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
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return 'вы уже зарегистрированы'

    state = request.args.get('state') or request.form.get('role')
    if not state or state not in ['volunteer', 'organization']:
        return redirect(url_for('register', state='volunteer'))

    volunteer_form = VolunteerRegisterForm()
    org_form = OrgRegisterForm()
    form = org_form if state == 'organization' else volunteer_form

    if form.validate_on_submit():
        error = check_form(form)
        if error:
            return render_template('register.html', volunteer_form=volunteer_form,
                                   org_form=org_form, state=state, error=error)

        if state == 'volunteer':
            user_data = {
                'name': form.name.data,
                'email': form.email.data,
                'phone_number': form.phone_number.data,
                'birth_date': form.birth_date.data.isoformat(),
                'info': form.info.data,
                'role_id': 1,
                'password': form.password.data
            }
        else:
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
        code = str(random.randint(0, 999999)).zfill(6)
        session['code'] = code
        return redirect("/verification")

    return render_template('register.html', volunteer_form=volunteer_form,
                           org_form=org_form, state=state, error=None)


@app.route('/verification', methods=['GET', 'POST'])
def verification():
    user_data = session.get('user_data')
    code = session.get('code')
    if not user_data or not code:
        return redirect(url_for('register', state='volunteer'))
    print(code) # потом будет отправка на почту
    form = VerifForm()
    if request.method == 'GET':
        return render_template('verification.html', form=form)
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
                if isinstance(user_data['birth_date'], datetime.date):
                    user.birth_date = user_data['birth_date']
                else:
                    user.birth_date = datetime.date.fromisoformat(user_data['birth_date'])
            db_sess = db_session.create_session()
            db_sess.add(user)
            db_sess.commit()
            login_user(user)
            return redirect('/')
        return 'нет'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
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
    if not task:
        return redirect('/tasks')
    role_id = current_user.role_id if current_user.is_authenticated else None
    description_lines = []
    organizer = ''
    organizer_phone = ''
    for line in (task.info or '').splitlines():
        if line.startswith('Организатор:'):
            organizer = line.replace('Организатор:', '', 1).strip()
        elif line.startswith('Телефон организатора:'):
            organizer_phone = line.replace('Телефон организатора:', '', 1).strip()
        else:
            description_lines.append(line)
    description = '\n'.join(description_lines).strip()
    return render_template('task.html', task=task, role_id=role_id,
                           description=description, organizer=organizer,
                           organizer_phone=organizer_phone)


@app.route('/take_part/<int:task_id>')
@login_required
def take_part(task_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == task_id).first()
    if not task or current_user.role_id != 1 or task.is_archived == True:
        return redirect(url_for('task', task_id=task_id))
    user_task = db_sess.query(UserTask).filter(UserTask.task_id == task_id,
                                               UserTask.user_id == current_user.id).first()
    if user_task:
        return redirect(url_for('profile', user_id=current_user.id))
    user_task = UserTask(
        user_id=current_user.id,
        task_id=task_id
    )
    db_sess.add(user_task)
    db_sess.commit()
    return redirect(url_for('profile', user_id=current_user.id))


@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if current_user.role_id != 2:
        return 'отказано'
    form = CreateTaskForm()
    if form.validate_on_submit():
        organizer = request.form.get('organizer', '').strip()
        organizer_phone = request.form.get('organizer_phone', '').strip()
        task_info = form.info.data
        if organizer or organizer_phone:
            task_info = f'{task_info}\n\nОрганизатор: {organizer}\nТелефон организатора: {organizer_phone}'
        task = Task(
            name=form.name.data,
            info=task_info,
            url_pic=None,
            start_date=form.start_date.data,
            end_date=form.start_date.data,
            address=form.address.data,
            people_count=form.people_count.data,
            tags=form.tags.data
        )
        db_sess = db_session.create_session()
        db_sess.add(task)
        db_sess.commit()
        if form.files.data and form.files.data[0].filename:
            files = []
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'tasks', str(task.id)), exist_ok=True)
            for f in form.files.data:
                filename = secure_filename(f.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], 'tasks', str(task.id), filename)
                f.save(path)
                files.append(f'upload/tasks/{task.id}/{filename}')
            task.url_pic = ','.join(files)
            db_sess.commit()
        return redirect('/tasks')
    return render_template('create_task.html', form=form)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        return redirect('/')
    tasks = []
    if user.role_id == 1:
        tasks_ids = db_sess.query(UserTask.task_id).filter(UserTask.user_id == user_id).all()
        for task_id in tasks_ids:
            task = db_sess.query(Task).filter(Task.id == task_id[0]).first()
            if task:
                tasks.append(task)
    elif user.role_id == 2:
        tasks = db_sess.query(Task).filter(Task.is_archived == False).all()
    return render_template('profile.html', user=user, tasks=tasks)


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if is_admin(current_user):
            return redirect('/admin_panel')
        else:
            return 'отказано'
    db_sess = db_session.create_session()
    admin = db_sess.query(User).filter(User.role_id == 3).first()
    form = AdminLoginForm()
    if form.validate_on_submit():
        if form.email.data == admin.email and admin.check_password(form.password.data):
            login_user(admin, remember=form.remember_me.data)
            return redirect('/admin_panel')
    return render_template('login.html', form=form, admin=True)


@app.route('/admin_panel')
@login_required
def admin_panel():
    if current_user.role_id != 3:
        return 'отказано'
    db_sess = db_session.create_session()
    tasks = db_sess.query(Task).filter(Task.is_archived == False).all()
    return render_template('admin_panel.html', tasks=tasks)


@app.route('/accept_task/<int:task_id>', methods=['POST'])
@login_required
def accept_task(task_id):
    if current_user.role_id != 3:
        return 'Доступ запрещен. Только для администраторов.', 403

    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == task_id).first()

    if not task:
        return 'Задание не найдено', 404

    return redirect(url_for('admin_panel'))


@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == task_id).first()

    if not task:
        return 'Задание не найдено', 404

    if current_user.role_id != 3 and current_user.role_id != 2:
        return 'Доступ запрещен. Только автор или администратор могут удалить задание.', 403

    db_sess.query(UserTask).filter(UserTask.task_id == task_id).delete()

    db_sess.delete(task)
    db_sess.commit()

    if current_user.role_id == 3:
        return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('profile', user_id=current_user.id))



if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='127.0.0.1', port=5001, debug=True)
