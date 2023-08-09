# The settings in this file are secondary to .env, which overrides

# Assume production by default, unset debug and testing state
FLASK_DEBUG=false
FLASK_DEBUG_TB_ENABLED=false
FLASK_TESTING=false

# To only support HTTPS, set Secure Cookies to True
FLASK_SESSION_COOKIE_SECURE=true

# --- App configuration
# Default timezone when user timezone is not known
FLASK_TIMEZONE='Asia/Kolkata'
FLASK_ASSET_MANIFEST_PATH=static/build/manifest.json
# Asset base path – without a trailing slash
FLASK_ASSET_BASE_PATH=/static/build
FLASK_STATIC_SUBDOMAIN=static
