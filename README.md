# Foodgram — продуктовый помощник

Foodgram — приложение для публикации рецептов, подписок на авторов, избранного и списка покупок.

## Автор

Фролов Никита Сергеевич — [GitHub HYPKA1](https://github.com/HYPKA1).

## Технологии

Python 3.12, Django 5.2, DRF, Djoser, django-filter, PostgreSQL 16, Gunicorn, Docker Compose, Nginx, React.

## Ссылки

- [Сайт Foodgram](https://51-250-65-215.sslip.io/)
- [Документация API](https://51-250-65-215.sslip.io/api/docs/)
- [Админка](https://51-250-65-215.sslip.io/admin/)
- [Репозиторий](https://github.com/HYPKA1/foodgram)

Замените `YOUR_DOMAIN` на адрес после настройки HTTPS на сервере.

## Запуск с Docker Compose

```bash
git clone https://github.com/HYPKA1/foodgram.git
cd foodgram/infra
```

Создайте `.env` из параметров окружения развёртывания. Обязательные секреты: `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY`; имя базы и пользователя должны совпадать с настройками Compose.

```bash
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
docker compose -f docker-compose.production.yml exec backend python manage.py import_tags
```

## Локальный запуск без Docker

Установите Python 3.12 и PostgreSQL 16; подготовьте базу и пользователя согласно настройкам PostgreSQL.

```bash
git clone https://github.com/HYPKA1/foodgram.git
cd foodgram/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_ingredients
python manage.py import_tags
python manage.py runserver
```

Подключение к PostgreSQL определяется переменными окружения с установленными в `settings.py` значениями по умолчанию. Для локального запуска используется конфигурация установленного PostgreSQL.
