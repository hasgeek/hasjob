import re

#: The title of this site
SITE_TITLE = 'Job Board'
#: TypeKit code for fonts
TYPEKIT_CODE = ''
#: Google Analytics code UA-XXXXXX-X
GA_CODE = ''
#: Database backend
SQLALCHEMY_DATABASE_URI = 'sqlite:///'
#: Secret key
SECRET_KEY = 'make this something random'  # nosec B105
#: Timezone
TIMEZONE = 'Asia/Kolkata'
#: Static resource subdomain (defaults to 'static')
STATIC_SUBDOMAIN = 'static'
#: Upload path
UPLOADED_LOGOS_DEST = '/tmp/uploads'  # nosec B108
#: Cache settings
CACHE_TYPE = 'redis'
#: RQ settings
RQ_REDIS_URL = 'redis://localhost:6379/0'
RQ_SCHEDULER_INTERVAL = 1
#: GeoIP database file (GeoIP2 or GeoLite2 city mmdb)
#: On Ubuntu: /usr/share/GeoIP/GeoLite2-City.mmdb
#: On Homebrew: /usr/local/var/GeoIP/GeoLite2-City.mmdb
GEOIP_PATH = '/usr/share/GeoIP/GeoLite2-City.mmdb'
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
# Mail sender for crash reports and other automated mail
DEFAULT_MAIL_SENDER = 'Hasjob <test@example.com>'
MAIL_DEFAULT_SENDER = DEFAULT_MAIL_SENDER
# Mail sender for job application responses (email address only)
MAIL_SENDER = 'test@example.com'
#: Logging: recipients of error emails
ADMINS = []
#: Log file
LOGFILE = 'error.log'
#: Use SSL for some URLs
USE_SSL = False
#: Twitter integration (register as a "client" app)
TWITTER_ENABLED = False
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''  # nosec B105
TWITTER_ACCESS_KEY = ''
TWITTER_ACCESS_SECRET = ''  # nosec B105
#: Bit.ly integration for short URLs
BITLY_USER = ''
BITLY_KEY = ''
#: Access key for periodic server-only tasks
PERIODIC_KEY = ''
#: Throttle limit for email domain
THROTTLE_LIMIT = 5
#: Don't show year for dates within this many days
SHORTDATE_THRESHOLD_DAYS = 60
#: Email address to display when asking users to contact support
SUPPORT_EMAIL = 'support@hasgeek.com'
#: Words banned in the title and their error messages
BANNED_WORDS = [
    [
        ['awesome'],
        'We’ve had a bit too much awesome around here lately. Got another adjective?',
    ],
    [
        ['rockstar', 'rock star', 'rock-star'],
        'You are not rich enough to hire a rockstar. Got another adjective?',
    ],
    [
        ['superstar', 'super star'],
        'Everyone around here is a superstar. The term is redundant.',
    ],
    [
        ['kickass', 'kick ass', 'kick-ass', 'kicka$$', 'kick-a$$', 'kick a$$'],
        'We don’t condone kicking asses around here. Got another adjective?',
    ],
    [['ninja'], 'Ninjas kill people. We can’t allow that. Got another adjective?'],
    [
        ['urgent', 'immediate', 'emergency'],
        'Sorry, we can’t help with urgent or immediate requirements. Geeks don’t grow on trees',
    ],
    [['passionate'], 'Passion is implicit. Why even ask? Try another adjective?'],
    [['amazing'], 'Everybody’s amazing around here. The adjective is redundant.'],
    [
        ['fodu'],
        'We don’t know what you mean, but that sounds like a dirty word. Got another adjective?',
    ],
    [
        ['sick'],
        'Need an ambulance? Call 102, 108, 112 or 1298. One of those should work.',
    ],
    [['killer'], 'Murder is illegal. Don’t make us call the cops.'],
    [
        ['iit', 'iitian', 'iit-ian', 'iim', 'bits', 'bitsian'],
        'Q: How do you know someone is from IIT/IIM/BITS? A: They remind you all the time. Don’t be that person.',
    ],
]
#: URLs we don't accept, with accompanying error messages
INVALID_URLS = [
    (
        [
            re.compile(r'.*\.recruiterbox\.com/jobs'),
            re.compile(r'hire\.jobvite\.com/'),
            re.compile(r'bullhornreach\.com/job/'),
            re.compile(r'linkedin\.com/jobs'),
            re.compile(r'freelancer\.com'),
            re.compile(r'hirist\.com/j/'),
            re.compile(r'iimjobs\.com/j/'),
            re.compile(r'.*\.workable.com/jobs'),
        ],
        "Candidates must apply via Hasjob",
    )
]
#: LastUser server
LASTUSER_SERVER = 'https://hasgeek.com/'
#: LastUser client id
LASTUSER_CLIENT_ID = ''
#: LastUser client secret
LASTUSER_CLIENT_SECRET = ''  # nosec B105
