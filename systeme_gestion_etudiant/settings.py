"""
Django settings for systeme_gestion_etudiant project.
"""


import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-1ie^!2y7u3w$u*ln^46hcle15#hh8m%!r_75et70h(^n_yafwc'

DEBUG = True
ALLOWED_HOSTS = ["votre-domaine.com", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']



MEDIA_URL="/media/"
MEDIA_ROOT=os.path.join(BASE_DIR,"media")


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGIN_REDIRECT_URL = '/'


# Configuration des sessions
SESSION_COOKIE_AGE = 3600  # 1 heure en secondes
SESSION_SAVE_EVERY_REQUEST = True
# Application definition

INSTALLED_APPS = [
    # Applications par défaut de Django :
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',  # <--- AJOUTEZ CETTE LIGNE
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'systeme_etudiant_app',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'systeme_etudiant_app.LoginCheckMiddleware.LoginCheckMiddleWare',
    'systeme_etudiant_app.LoginCheckMiddleware.StudentApprovalMiddleware',
    # corrigé
]


ROOT_URLCONF = 'systeme_gestion_etudiant.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['systeme_etudiant_app/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'systeme_etudiant_app.context_processors.admin_pending_count',
                'systeme_etudiant_app.context_processors.admin_notifications',
                'django.template.context_processors.media',
                'django.template.context_processors.static',

            ],
        },
    },
]

WSGI_APPLICATION = 'systeme_gestion_etudiant.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# 'USER': 'postgres',
#         'PASSWORD': 'Admin',
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'senegal_ucab',
        'USER': 'systeme_etudiant',
        'PASSWORD': 'mamesido07',  # À sécuriser en production
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=s_ope',
            'client_encoding': 'UTF8'  # Force l'encodage
        }
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/






AUTH_USER_MODEL = 'systeme_etudiant_app.CustomUser'


AUTHENTICATION_BACKENDS = [
    'systeme_etudiant_app.backends.EmailBackend',
]
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'Student Management System <no-reply@ucab.sn>'
EMAIL_FILE_PATH=os.path.join(BASE_DIR, "sent_mails")


# Envoi d’e-mails avec Gmail
# COMMENTEZ ces lignes temporairement :
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'diattas994@gmail.com'
# EMAIL_HOST_PASSWORD = 'mamesido010'
# DEFAULT_FROM_EMAIL = 'Student Management System <diattas994@gmail.com>'