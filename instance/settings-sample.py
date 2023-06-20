#: The title of this site
SITE_TITLE = 'Job Board'
#: TypeKit code for fonts
TYPEKIT_CODE = ''
#: Google Analytics code UA-XXXXXX-X
GA_CODE = ''
#: Asset server (optional)
ASSET_SERVER = ''
#: Database backend
SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
#: Secret key
SECRET_KEY = 'make this something random'  # nosec B105
#: Timezone
TIMEZONE = 'Asia/Kolkata'
#: Server host name (and port if not 80/443)
SERVER_NAME = 'hasjob.test:5001'
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
SUPPORT_EMAIL = 'person@example.com'
#: Sitemap key
SITEMAP_KEY = None
# Dogpile cache backend
DOGPILE_CACHE_BACKEND = 'dogpile.cache.redis'
# Dogpile cache backend URL
DOGPILE_CACHE_URLS = '127.0.0.1:6379'
# Dogpile cache regions (important, do not remove!)
DOGPILE_CACHE_REGIONS = [('hasjob_index', 3600)]
ASSET_MANIFEST_PATH = 'static/build/manifest.json'
# no trailing slash
ASSET_BASE_PATH = '/static/build'
