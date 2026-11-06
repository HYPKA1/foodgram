import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка ингредиентов из JSON в базу данных."""

    help = 'Загружает ингредиенты из data/ingredients.json'

    def handle(self, *args, **options):
        """Читает JSON и сохраняет ингредиенты."""

        file_path = (
            Path('/data/ingredients.json')
            if Path('/data/ingredients.json').exists()
            else settings.BASE_DIR.parent / 'data' / 'ingredients.json'
        )

        if not file_path.exists():
            self.stderr.write(
                self.style.ERROR(
                    f'Файл не найден: {file_path}'
                )
            )
            return

        with file_path.open(encoding='utf-8') as file:
            ingredients = json.load(file)

        created_count = 0
        existing_count = 0

        with transaction.atomic():
            for ingredient_data in ingredients:
                _, created = Ingredient.objects.get_or_create(
                    name=ingredient_data['name'],
                    measurement_unit=ingredient_data[
                        'measurement_unit'
                    ],
                )

                if created:
                    created_count += 1
                else:
                    existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена!\n'
                f'Добавлено ингредиентов: {created_count}\n'
                f'Уже существовали: {existing_count}\n'
                f'Всего в базе: {Ingredient.objects.count()}'
            )
        )
