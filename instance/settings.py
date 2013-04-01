# -*- coding: utf-8 -*-
#: The title of this site
SITE_TITLE='Job Board'
#: TypeKit code for fonts
TYPEKIT_CODE=''
#: Google Analytics code UA-XXXXXX-X
GA_CODE=''
#: Database backend
SQLALCHEMY_DATABASE_URI = 'sqlite:///'
#: Secret key
SECRET_KEY = 'make this something random'
#: Timezone
TIMEZONE = 'Asia/Calcutta'
#: Upload path
UPLOADED_LOGOS_DEST='/tmp/uploads'
#: Search index path
SEARCH_INDEX_PATH='/tmp/search'
#: Mail settings
#: MAIL_FAIL_SILENTLY : default True
#: MAIL_SERVER : default 'localhost'
#: MAIL_PORT : default 25
#: MAIL_USE_TLS : default False
#: MAIL_USE_SSL : default False
#: MAIL_USERNAME : default None
#: MAIL_PASSWORD : default None
#: DEFAULT_MAIL_SENDER : default None
MAIL_FAIL_SILENTLY = False
MAIL_SERVER = 'localhost'
DEFAULT_MAIL_SENDER = ('Job Board', 'test@example.com')
MAIL_USERNAME = None
MAIL_PASSWORD = None
#: Logging: recipients of error emails
ADMINS = []
#: Log file
LOGFILE = 'error.log'
#: Use SSL for some URLs
USE_SSL = False
#: Twitter integration (register as a "client" app)
TWITTER_ENABLED = False
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_KEY = ''
TWITTER_ACCESS_SECRET = ''
#: Bit.ly integration for short URLs
BITLY_USER = ''
BITLY_KEY = ''
#: Access key for periodic server-only tasks
PERIODIC_KEY = ''
#: Throttle limit for email domain
THROTTLE_LIMIT = 5
SUPPORT_EMAIL = 'support@hasgeek.com'
#: Words banned in the title and their error messages
BANNED_WORDS = [
    [['awesome'], u'We’ve had a bit too much awesome around here lately. Got another adjective?'],
    [['rockstar', 'rock star', 'rock-star'], u'You are not rich enough to hire a rockstar. Got another adjective?'],
    [['superstar', 'super star'], u'Everyone around here is a superstar. The term is redundant.'],
    [['kickass', 'kick ass', 'kick-ass', 'kicka$$', 'kick-a$$', 'kick a$$'], u'We don’t condone kicking asses around here. Got another adjective?'],
    [['ninja'], u'Ninjas kill people. We can’t allow that. Got another adjective?'],
    [['urgent', 'immediate'], u'Sorry, we can’t help with urgent or immediate requirements. Geeks don’t grow on trees'],
    [['passionate'], u'Passion is implicit. Why even ask? Try another adjective?'],
    [['amazing'], u'Everybody’s amazing around here. The adjective is redundant.'],
    [['fodu'], u'We don’t know what you mean, but that sounds like a dirty word. Got another adjective?'],
    [['sick'], u'Need an ambulance? Call 102, 108, 112 or 1298. One of those should work.']
]

#: LastUser server
LASTUSER_SERVER = 'https://auth.hasgeek.com/'
#: LastUser client id
LASTUSER_CLIENT_ID = ''
#: LastUser client secret
LASTUSER_CLIENT_SECRET = ''
