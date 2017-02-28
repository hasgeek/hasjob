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
SECRET_KEY = 'make this something random'
#: Timezone
TIMEZONE = 'Asia/Kolkata'
#: Server host name (and port if not 80/443)
SERVER_NAME = 'hasjob.local'
#: Static resource subdomain (defaults to 'static')
STATIC_SUBDOMAIN = 'static'
#: Upload path
UPLOADED_LOGOS_DEST = '/tmp/uploads'
#: Hascore server
HASCORE_SERVER = 'https://api.hasgeek.com/'
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
SUPPORT_EMAIL = 'person@example.com'
#: Sitemap key
SITEMAP_KEY = None
DOGPILE_CACHE_URLS = "http://127.0.0.1:6379"
DOGPILE_CACHE_REGIONS = [
    ('hour', 3600),
    ('hasjob_index', 3600),
    ('day', 3600 * 24),
    ('month', 3600 * 24 * 31),
]
DOGPILE_CACHE_BACKEND = 'dogpile.cache.redis'
