#!/bin/sh

set -eu

cd "$(dirname "$0")/.."

BACKUP_DIR="$PWD/backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

mkdir -p "$BACKUP_DIR"

echo "Создаём резервную копию PostgreSQL..."

DB_BACKUP="$BACKUP_DIR/foodgram_db_$DATE.sql"
MEDIA_BACKUP="$BACKUP_DIR/foodgram_media_$DATE.tar.gz"

if ! docker compose -f docker-compose.production.yml exec -T db \
    sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    > "$DB_BACKUP"; then
    rm -f "$DB_BACKUP"
    echo "Ошибка резервного копирования PostgreSQL"
    exit 1
fi

echo "Создаём резервную копию фотографий..."

MEDIA_VOLUME=$(docker compose -f docker-compose.production.yml \
    config --format json | python3 -c '
import json
import sys

config = json.load(sys.stdin)
print(config["services"]["backend"]["volumes"][1]["source"])
')

if ! docker run --rm \
    -v "$MEDIA_VOLUME:/media:ro" \
    -v "$BACKUP_DIR:/backup" \
    alpine:3.20 \
    tar -czf "/backup/$(basename "$MEDIA_BACKUP")" -C /media .; then
    rm -f "$MEDIA_BACKUP"
    echo "Ошибка резервного копирования фотографий"
    exit 1
fi

echo "Резервное копирование завершено!"
echo "База: $DB_BACKUP"
echo "Фотографии: $MEDIA_BACKUP"
