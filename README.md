# Foodgram — продуктовый помощник

Foodgram — веб-приложение для публикации рецептов. Пользователи могут подписываться на авторов, добавлять рецепты в избранное, собирать список покупок и скачивать его в TXT.

## Автор

**ФИО автора:** Фролов Никита Сергеевич.
**Контакт:** [GitHub — HYPKA1](https://github.com/HYPKA1).

## Технологии

Python 3.12, Django 5.2, Django REST Framework, Djoser, django-filter, PostgreSQL 16, Gunicorn, Docker Compose, Nginx, React.

## Ссылки на развёрнутый проект

- [Foodgram — сайт](http://51.250.65.215/)
- [Документация API](http://51.250.65.215/api/docs/)
- [Административная панель](http://51.250.65.215/admin/)
- [Исходный код](https://github.com/HYPKA1/foodgram)

Адрес учебной виртуальной машины временный: ссылки работают только при включённой ВМ и неизменном IP.

## Развёртывание через Docker Compose

Требуются Docker и Docker Compose. В каталоге `infra` создайте `.env` с параметрами PostgreSQL и Django:

```dotenv
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=REPLACE_WITH_STRONG_PASSWORD
POSTGRES_HOST=db
POSTGRES_PORT=5432
DJANGO_SECRET_KEY=REPLACE_WITH_RANDOM_SECRET
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend,YOUR_SERVER_IP
DJANGO_CSRF_TRUSTED_ORIGINS=http://YOUR_SERVER_IP
DJANGO_USE_HTTPS=False
```

Не публикуйте настоящий `.env` в Git.

Из каталога проекта:

```bash
cd infra
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d
```

Контейнер backend запускает миграции и `collectstatic` автоматически. Для **нового развёртывания с пустой БД** загрузите данные:

```bash
docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
docker compose -f docker-compose.production.yml exec backend python manage.py import_tags
```

Для просмотра статуса и логов:

```bash
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs --tail=100 backend
```

> **Важно для обновления старого сервера.** После объединения приложений `users` и `recipes` изменены имя таблицы пользователей и история миграций. Эти команды предназначены для **чистой БД**. Нельзя обновлять существующую БД с пользовательскими данными без отдельной проверенной миграции или переноса данных из резервной копии.

## Локальная установка без Docker

Потребуются Python 3.12 и запущенный PostgreSQL 16. Создайте в PostgreSQL роль `foodgram`, базу `foodgram`, назначьте роль владельцем базы. Например, под администратором PostgreSQL:

```sql
CREATE USER foodgram WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE foodgram OWNER foodgram;
```

В терминале из корня репозитория:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
export POSTGRES_DB=foodgram
export POSTGRES_USER=foodgram
export POSTGRES_PASSWORD=CHANGE_ME
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export DJANGO_SECRET_KEY=YOUR_LOCAL_SECRET
export DJANGO_DEBUG=True
python manage.py migrate
python manage.py import_ingredients
python manage.py import_tags
python manage.py runserver
```

Сервер доступен по адресу [http://127.0.0.1:8000/](http://127.0.0.1:8000/), административная панель — [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/). Для доступа в админку создайте пользователя командой:

```bash
python manage.py createsuperuser
```

Без явных переменных окружения в `settings.py` по умолчанию используются PostgreSQL и `DEBUG=False`. SQLite можно включить только явно, задав `DJANGO_DB_ENGINE=sqlite`; этот режим подходит для временных локальных тестов, а не для развёртывания по ТЗ.

## API

Документация API доступна по маршруту `/api/docs/`. Основные разделы: пользователи и подписки `/api/users/`, рецепты `/api/recipes/`, продукты `/api/ingredients/`, теги `/api/tags/`. Токенная авторизация осуществляется через Djoser.
