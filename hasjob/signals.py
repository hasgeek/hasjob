# -*- coding: utf-8 -*-

from blinker import Namespace
from flask import current_app

signals = Namespace()

signal_login = signals.signal('login')
signal_logout = signals.signal('logout')
signal_post_confirmed = signals.signal('post-confirmed')


@signal_login.connect
def login(user):
    current_app.logger.info("User Login: %r" % user)


@signal_logout.connect
def logout(user):
    current_app.logger.info("User Logout: %r" % user)
