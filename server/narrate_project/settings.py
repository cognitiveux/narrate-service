from datetime import timedelta

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ["SECRET_KEY_NARRATE_PROJECT"]

DEBUG = True
# DEBUG = False

ALLOWED_HOSTS = [
	"localhost",
	"*",
]

INSTALLED_APPS = [
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.messages",
	"django.contrib.staticfiles",
	"rest_framework_simplejwt.token_blacklist",
	"corsheaders",
	"backend",
	"rest_framework",
	"drf_yasg",
	"django_extensions",
	"django_celery_results",
]

MIDDLEWARE = [
	"corsheaders.middleware.CorsMiddleware",
	"django.middleware.security.SecurityMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "narrate_project.urls"

TEMPLATES = [
	{
		"BACKEND": "django.template.backends.django.DjangoTemplates",
		"DIRS": [],
		"APP_DIRS": True,
		"OPTIONS": {
			"context_processors": [
				"django.template.context_processors.debug",
				"django.template.context_processors.request",
				"django.contrib.auth.context_processors.auth",
				"django.contrib.messages.context_processors.messages",
			],
		},
	},
]

WSGI_APPLICATION = "narrate_project.wsgi.application"

DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.postgresql",
		"NAME": "postgres",
		"USER": "postgres",
		"HOST": "narrate-postgres",
		"PORT": 5432,
		"PASSWORD": "$g$5tG7eBT4Yu%?C!$70)2^8wSUjfqQWUv4zgetGNA&4B#G_V#dHzCm*fQ-H"
	}
}

AUTH_PASSWORD_VALIDATORS = [
	{
		"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
	},
	{
		"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
	},
	{
		"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
	},
	{
		"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
	},
]

REST_FRAMEWORK = {
	"EXCEPTION_HANDLER": "backend.exceptions.custom_exception_handler",
	"DEFAULT_AUTHENTICATION_CLASSES": [
		"rest_framework_simplejwt.authentication.JWTAuthentication",
		"rest_framework.authentication.SessionAuthentication",
	],
}

SWAGGER_SETTINGS = {
	"SECURITY_DEFINITIONS": {
		"Bearer": {
			"type": "apiKey",
			"name": "Authorization",
			"in": "header"
		}
	},
   "USE_SESSION_AUTH": True,
   "DEFAULT_MODEL_DEPTH": -1,
   "DEFAULT_MODEL_RENDERING": "example",
}

SIMPLE_JWT = {
	"ALGORITHM": "HS256",
	"SIGNING_KEY": SECRET_KEY,
	"USER_ID_CLAIM": "user_id",
	"ACCESS_TOKEN_LIFETIME": timedelta(days=60),
	"REFRESH_TOKEN_LIFETIME": timedelta(days=365),
	"AUDIENCE": ["AUTH", "IHU", "KMKD", "SUSKO",],
	"AUTH_COOKIE": "access_token",
	"AUTH_REFRESH_COOKIE": "refresh_token",
	"AUTH_COOKIE_DOMAIN": None,
	"AUTH_COOKIE_SECURE": False,
	"AUTH_COOKIE_HTTP_ONLY" : True,
	"AUTH_COOKIE_PATH": "/",
	"AUTH_COOKIE_SAMESITE": "Strict",
}

AUTH_USER_MODEL = "backend.Users"

PASSWORD_HASHERS = [
	"django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

CELERY_TIMEZONE = TIME_ZONE
CELERY_RESULT_BACKEND = "django-db"
CELERYD_STATE_DB = "./celery_worker_state"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_INTERVAL = 0.5
CELERY_TASK_TIME_LIMIT = 1000

LOGGER_PATH = "./narrate_project.log"

GLOBAL_SETTINGS = {
	"FROM_EMAIL": os.environ["SERVER_EMAIL"],
	"FROM_EMAIL_ALIAS": os.environ["SERVER_EMAIL_ALIAS"],
	"EMAIL_PASSWORD": os.environ["SERVER_EMAIL_PASSWORD"],
}

MODEL_MAPPING = {
	"RESET_PASSWORD": {
		"model_class": "ResetPassword",
		"resource_name": "user"
	}
}

EMAIL_COUNTDOWN_SEC = 1
FREQUENT_REQUEST_COUNT_LIMIT = 5
ACTIVATE_ACCOUNT_BASE_URL = "http://localhost:10000/backend/activate_account"
RESET_PASSWORD_BASE_URL = "http://localhost:10000/backend/reset_password"
RESET_PASSWORD_INTERVAL = 3600
RESET_PASSWORD_SIGNATURE_MAX_AGE_SEC = 1800

MEDIA_FORMAT_2D = ["png", "jpeg", "jpg", "gif", "tiff", "tif", "psd", "pdf", "eps", "ai", "indd", "raw", "bmp", "svg", "webp", "ico", "apng", "avif", "heif", "heic",]

MEDIA_IMAGE_2D = ["png", "jpeg", "jpg", "gif", "tiff", "tif", "bmp", "svg", "webp", "ico", "apng", "avif", "heif", "heic",]

PROTECTED_MEDIA_ROOT = os.path.join(BASE_DIR, "protected_media/")

# Redirect to HTTPS
# SECURE_SSL_REDIRECT = True

# Swagger HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CORS config
#CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = []

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 3600

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"