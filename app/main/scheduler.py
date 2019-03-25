#!/usr/bin/env python
# coding=UTF-8
'''
@Author: LogicJake
@Date: 2019-03-24 14:32:34
@LastEditTime: 2019-03-25 21:56:49
'''
from datetime import datetime

from apscheduler.jobstores.base import JobLookupError

from app import app, db, scheduler
from app.main.selector.selector_handler import new_handler
from app.models.notification import Notification
from app.models.task import Task
from app.models.task_status import TaskStatus


def get_content(url, is_chrome, selector_type, selector):
    if is_chrome == 'no':
        selector_handler = new_handler('request')

        if selector_type == 'xpath':
            return selector_handler.get_by_xpath(url, selector)
    else:
        selector_handler = new_handler('phantomjs')

        if selector_type == 'xpath':
            return selector_handler.get_by_xpath(url, selector)


def wraper_msg(title, content):
    header = title
    content = content
    return header, content


def send_message(id, content):
    from app.main.notification.notification_handler import new_handler

    task = Task.query.filter_by(id=id).first()
    mail = task.mail
    telegrame = task.telegrame
    name = task.name

    header, content = wraper_msg(name, content)

    if mail == 'yes':
        handler = new_handler('mail')
        mail_info = Notification.query.filter_by(type='mail').first()
        mail_address = mail_info.number
        handler.send(mail_address, header, content)

    if telegrame == 'yes':
        handler = new_handler('telegrame')
        mail_info = Notification.query.filter_by(type='telegrame').first()
        mail_address = mail_info.number
        handler.send(mail_address, header, content)


def monitor(id, url, selector_type, selector, is_chrome):
    with app.app_context():
        status = '成功'
        try:
            content = get_content(url, is_chrome, selector_type, selector)
            send_message(id, content)
        except Exception as e:
            status = repr(e)

        task_status = TaskStatus.query.filter_by(id=id).first()
        task_status.last_run = datetime.now()
        task_status.last_status = status
        db.session.add(task_status)
        db.session.commit()


def add_job(id, url, selector_type, selector, is_chrome, interval):
    scheduler.add_job(
        func=monitor,
        args=(
            id,
            url,
            selector_type,
            selector,
            is_chrome,
        ),
        trigger='interval',
        minutes=interval,
        id='task_{}'.format(id),
        replace_existing=True)


def remove_job(id):
    try:
        scheduler.remove_job('task_{}'.format(id))
    except JobLookupError:
        pass


def is_job_exist(id):
    jobs = scheduler.get_jobs()
    for job in jobs:
        if job.id == 'task_{}'.format(id):
            return True

    return False
