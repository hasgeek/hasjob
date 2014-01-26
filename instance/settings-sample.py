#: The title of this site
SITE_TITLE = 'Job Board'
#: TypeKit code for fonts
TYPEKIT_CODE = ''
#: Google Analytics code UA-XXXXXX-X
GA_CODE = ''
#: Database backend
SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
#: Secret key
SECRET_KEY = 'make this something random'
#: Timezone
TIMEZONE = 'Asia/Calcutta'
#: Upload path
UPLOADED_LOGOS_DEST = '/tmp/uploads'
#: Search index path
SEARCH_INDEX_PATH = '/tmp/search'
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

# Consumer key for uploading and accessing documents on Docspad
DOCSPAD_CONSUMER_KEY=''

# Upload directory for temporary storing files (until they are forwarded to docspad)
TMP_UPLOAD_DIR = '/tmp'
