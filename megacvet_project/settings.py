# megacvet_project/settings.py

import os
from pathlib import Path
import dj_database_url # Добавьте этот импорт

from pathlib import Path

from dotenv import load_dotenv  # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
load_dotenv()                   # <-- И ЭТУ СТРОКУ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# --- Секретный ключ ---
# Забираем ключ из переменных окружения
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-default-secret-key-for-development')
# SECRET_KEY = os.environ.get('django-insecure-8$n0drft1v!r0ox=rqgcc&2x00&yzt@#y%(t87p21my2aaqdry')
#SECRET_KEY = 'django-insecure-8$n0drft1v!r0ox=rqgcc&2x00&yzt@#y%(t87p21my2aaqdry'

# SECURITY WARNING: don't run with debug turned on in production!
# --- Режим отладки ---
# DEBUG будет True только если переменная окружения DJANGO_DEBUG установлена в 'True'
# DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
DEBUG = True

# --- Разрешенные хосты ---
# Укажите IP-адрес вашего сервера и доменное имя
# ALLOWED_HOSTS = ['your_server_ip', 'www.yourdomain.com', 'yourdomain.com']
ALLOWED_HOSTS = ['109.120.142.26', '127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    'shop',  # Наше новое приложение
    'cart', # Наше новое приложение
    'orders', # Наше новое приложение
    'users', # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
    'imagekit', # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'megacvet_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'megacvet_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Если на сервере есть переменная DATABASE_URL, используем ее
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=False)


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

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# --- Настройки статических файлов ---
STATIC_URL = 'static/'
# Новая настройка: куда собирать все статические файлы
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Указываем Django, где еще искать статические файлы
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# megacvet_project/settings.py (в конце файла)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CART_SESSION_ID = 'cart'

# URL-адрес, на который Django будет перенаправлять после успешного входа
LOGIN_REDIRECT_URL = '/'

# URL-адрес, на который Django будет перенаправлять после выхода из системы
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = [
    # 1. Сначала пытаемся войти по email (наш новый бэкенд)
    'users.backends.EmailBackend',  # <-- Замените 'accounts' на 'users', если у вас папка называется users

    # 2. Если не получилось, пытаемся войти по username (стандартный бэкенд)
    # Это нужно, чтобы суперпользователь мог по-прежнему входить в админку.
    'django.contrib.auth.backends.ModelBackend',
]

# --- НАСТРОЙКИ ДЛЯ ОТПРАВКИ EMAIL ---
# Используем консольный бэкенд для отладки, если не заданы другие настройки
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Настоящие настройки для отправки через SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')         # smtp.gmail.com
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER') # Ваш email (example@gmail.com)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD') # Ваш 16-значный пароль приложения

