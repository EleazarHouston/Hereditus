from typing import Any, cast

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import LOG_DIR, env
from .base import LOGGING as BASE_LOGGING

if not env("DATABASE_URL", default=""):
    raise ImproperlyConfigured("DATABASE_URL is required in production")
if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("SECRET_KEY is required in production")
if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("ALLOWED_HOSTS is required in production")

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging_config = cast(dict[str, Any], BASE_LOGGING)  # noqa: F405
logging_config["handlers"]["file"] = {
    "class": "logging.FileHandler",
    "filename": LOG_DIR / "hereditus.log",
    "formatter": "verbose",
}
logging_config["loggers"]["hereditus"]["handlers"].append("file")
LOGGING = logging_config
