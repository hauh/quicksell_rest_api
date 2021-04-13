"""
Django settings for quicksell project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [os.environ['ALLOWED_HOSTS']]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

AUTH_USER_MODEL = 'quicksell_app.User'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

ROOT_URLCONF = 'quicksell.urls'
WSGI_APPLICATION = 'quicksell.wsgi.application'


# Application definition

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',

	'rest_framework',
	'rest_framework.authtoken',
	'mptt',
	'drf_yasg',
	'silk',
	'fcm_django',

	'quicksell_app',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'whitenoise.middleware.WhiteNoiseMiddleware',
	'silk.middleware.SilkyMiddleware',

	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': os.environ['POSTGRES_DB'],
		'USER': os.environ['POSTGRES_USER'],
		'PASSWORD': os.environ['POSTGRES_PASSWORD'],
		'HOST': 'quicksell_db',
		'PORT': 5432,

		# # for tests
		# 'ENGINE': 'django.db.backends.sqlite3',
		# 'NAME': 'test_db',
	},
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
	{'NAME': 'django.contrib.auth.password_validation.' + validator_name}
	for validator_name in (
		'UserAttributeSimilarityValidator',
		'MinimumLengthValidator',
		'CommonPasswordValidator',
		'NumericPasswordValidator',
	)
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
# USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'


# Django Rest Framework

REST_FRAMEWORK = {
	'DEFAULT_METADATA_CLASS': 'quicksell_app.misc.NoMetadata',
	'DEFAULT_PERMISSION_CLASSES': (
		'rest_framework.permissions.IsAuthenticatedOrReadOnly',
	),
	'DEFAULT_PARSER_CLASSES': (
		'rest_framework.parsers.JSONParser',
	),
	'DEFAULT_AUTHENTICATION_CLASSES': (
		'rest_framework.authentication.TokenAuthentication',
	),
	'DEFAULT_VERSIONING_CLASS':
		'rest_framework.versioning.AcceptHeaderVersioning',
	'TEST_REQUEST_DEFAULT_FORMAT': 'json',
	'DEFAULT_THROTTLE_RATES': {
		'password_reset.day': '50/day',
		'password_reset.hour': '15/hour'
	},
	'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
	'PAGE_SIZE': 10
}


# Emails

DEFAULT_FROM_EMAIL = 'Quicksell Mailer <noreply@quicksell.ru>'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_USE_TLS = False


# Swagger

SWAGGER_SETTINGS = {
	'SECURITY_DEFINITIONS': {
		'Token': {
			'type': 'apiKey',
			'name': 'Authorization',
			'in': 'header'
		}
	},
	'DEFAULT_AUTO_SCHEMA_CLASS': 'quicksell_app.schema.FilteringFieldsAutoSchema',
	'DEFAULT_INFO': 'quicksell_app.schema.schema_info'
}


# Firebase Cloud Messaging

FCM_DJANGO_SETTINGS = {
	'APP_VERBOSE_NAME': "Quicksell App",
	'FCM_SERVER_KEY': os.environ['FCM_KEY'],
	'ONE_DEVICE_PER_USER': False,
	'DELETE_INACTIVE_DEVICES': False,
}
