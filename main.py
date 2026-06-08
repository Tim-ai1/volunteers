from flask import Flask, redirect
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
    user_form = UserRegisterForm()
    org_form = OrgRegisterForm()
    # if form.validate_on_submit():
    #     if form.password.data != form.password_again.data:
    #         return render_template('register.html', title='Регистрация',
    #                                form=form,
    #                                message="Пароли не совпадают")
    #     db_sess = db_session.create_session()
    #     if db_sess.query(User).filter(User.email == form.email.data).first():
    #         return render_template('register.html', title='Регистрация',
    #                                form=form,
    #                                message="Пользователь с таким электронным адресом уже есть")
    #     if db_sess.query(User).filter(User.username == form.username.data).first():
    #         return render_template('register.html', title='Регистрация',
    #                                form=form,
    #                                message="Пользователь с таким именем уже есть")
    #     user = User(
    #         username=form.username.data,
    #         email=form.email.data,
    #         birth_date=form.birth_date.data,
    #         info=form.info.data,
    #         pfp=None,
    #     )
    #     user.set_password(form.password.data)
    #     db_sess.add(user)
    #     db_sess.commit()
    #     if form.pfp.data:
    #         f = form.pfp.data
    #         filename = secure_filename(f.filename)
    #         os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pfp', str(user.id)))
    #         path = os.path.join(app.config['UPLOAD_FOLDER'], 'pfp', str(user.id), filename)
    #         f.save(path)
    #         pfp = filename
    #     else:
    #         pfp = None
    #
    #     user.pfp = pfp
    #     db_sess.commit()
    #     return redirect('/login')
    # return render_template('register.html', title='Регистрация', form=form)


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run()