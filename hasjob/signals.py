from blinker import Namespace

signals = Namespace()

signal_login = signals.signal('login')
signal_logout = signals.signal('logout')
signal_post_confirmed = signals.signal('post-confirmed')
