"""
Django settings for eos_accounts project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
from django.utils._os import safe_join
import raven

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = 'templates'

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
if os.path.exists(safe_join(BASE_DIR, 'eos_accounts/live.py')):
    # if this file exists, we're on the live server
    DEBUG = False
    LIVE = True
    STAGING = False


ALLOWED_HOSTS = ['localhost', 'eos-account-creator.com', 'preview.eos-account-creator.com', '192.168.0.26', '192.168.0.73', '192.168.0.206', '192.168.0.23', '127.0.0.1']
CANONICAL_BASE_URL = 'https://eos-account-creator.com/'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_countries',
    'buy',
]
if not DEBUG:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'eos_accounts.middleware.MyMiddleware',
     'django.middleware.cache.FetchFromCacheMiddleware',
]
if DEBUG:
    MIDDLEWARE += [
    'eos_accounts.middleware.TimeRequestsMiddleware',
    # 'eos_accounts.middleware.ConsoleExceptionMiddleware',
]

CACHE_MIDDLEWARE_SECONDS = 0

ROOT_URLCONF = 'eos_accounts.urls'

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
                'buy.views.add_price_context_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'eos_accounts.wsgi.application'

if DEBUG:
    CACHING_DURATION = 0
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }    
else:
    CACHING_DURATION = 60
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    'locale',
]

LANGUAGES = [
  ('en', 'English'),
  ('zh', '中文'),
]

GEOIP_PATH = safe_join(BASE_DIR, 'eos_accounts/')
GEOIP_COUNTRY = safe_join(BASE_DIR, 'eos_accounts/GeoLite2-Country.mmdb')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
STATIC_URL = '/static/'
STATIC_ROOT = '/django/static/'
ML = 512
EOS_API_NODES = ['https://eos.greymass.com']
NEWACCOUNT_RAM_KB = 3
NEWACCOUNT_NET_STAKE = 0.05
NEWACCOUNT_CPU_STAKE = 0.15
BURNED_KEYS = ("EOS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV", "EOS6qnCLMm5d67JdP11EF31Kf4UUNr6ktUKBqPsDhSXADT1CHfNG2", "EOS6vizDzpZMxtt27WVVCUVYEFHXgaLhEfPuLQAXfpAJaf2oWAcwg", "EOS7KKga2itCjyLAm6n4GHqujN4arBv3GQEWpZwQqSDWyNEj7iuxQ", "EOS6iBVEaRDS3mofUJpa8bjD94vohHrsSqqez1wcsWjhPpeNArfBF")

try:
    from eos_accounts.local_settings import *
except ImportError as e:
    pass
