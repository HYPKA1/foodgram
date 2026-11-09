"""Настройки Django для production."""

import os

from .settings import *  # noqa: F401, F403


# Секретный ключ берётся из переменных окружения.
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']


# В production подробные ошибки Django отключены.
DEBUG = False


# Разрешённые домены и IP-адреса.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ['DJANGO_ALLOWED_HOSTS'].split(',')
    if host.strip()
]


# Доверенные адреса для CSRF.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'DJANGO_CSRF_TRUSTED_ORIGINS', ''
    ).split(',')
    if origin.strip()
]


# Настройки безопасности HTTPS.
USE_HTTPS = os.environ.get(
    'DJANGO_USE_HTTPS', 'False'
).lower() == 'true'

if USE_HTTPS:
    SECURE_PROXY_SSL_HEADER = (
        'HTTP_X_FORWARDED_PROTO',
        'https',
    )

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_SECONDS = 3600
