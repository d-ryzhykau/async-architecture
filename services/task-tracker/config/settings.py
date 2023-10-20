"""
Django settings for task_tracker project.

Generated by 'django-admin startproject' using Django 4.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

import environ
import requests

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", cast=bool, default=False)

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # local
    "task_tracker.core",
    "task_tracker.tasks",
    "task_tracker.users",
    # default
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "mozilla_django_oidc",
    "widget_tweaks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": env.db("DATABASE_URL"),
}


AUTHENTICATION_BACKENDS = [
    "config.oidc.OIDCAuthenticationBackend",
]

AUTH_USER_MODEL = "users.User"

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


OIDC_RP_CLIENT_ID = env("OIDC_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = env("OIDC_CLIENT_SECRET")
OIDC_RP_SCOPES = "openid email profile"
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_AUTHENTICATE_CLASS = "config.oidc.OIDCAuthenticationRequestView"


def get_oidc_metadata(discovery_url: str) -> dict:
    response = requests.get(discovery_url)
    if not response.ok:
        raise ValueError("Failed to retrieve OpenID Connect metadata.")
    return response.json()


oidc_metadata = get_oidc_metadata(env("OIDC_DISCOVERY_URL"))
OIDC_OP_AUTHORIZATION_ENDPOINT = oidc_metadata["authorization_endpoint"]
OIDC_OP_TOKEN_ENDPOINT = oidc_metadata["token_endpoint"]
OIDC_OP_USER_ENDPOINT = oidc_metadata["userinfo_endpoint"]
OIDC_OP_JWKS_ENDPOINT = oidc_metadata["jwks_uri"]


LOGIN_URL = "oidc_authentication_init"
LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = oidc_metadata["end_session_endpoint"]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SESSION_COOKIE_NAME = "task_tracker-sessionid"
CSRF_COOKIE_NAME = "task_tracker-csrftoken"


SILENCED_SYSTEM_CHECKS = [
    "auth.W004",  # can be ignored because User.email is unique for all active Users
]