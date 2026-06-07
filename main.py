from flask import Flask
import datetime
from flask_apscheduler import APScheduler

from data import db_session
from data.tasks import Task
from data.users import User

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


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run()