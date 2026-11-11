import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class ImportJsonCommand(BaseCommand):
    """Общий быстрый импорт данных из JSON."""

    model = None
    filename = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--path', type=Path, default=None,
            help='Путь к JSON-файлу (необязательно)',
        )

    def handle(self, *args, **options):
        try:
            path = options['path'] or self.default_path()
            with path.open(encoding='utf-8') as source:
                records = json.load(source)
            before = self.model.objects.count()
            self.model.objects.bulk_create(
                (self.model(**record) for record in records),
                ignore_conflicts=True,
            )
            added = self.model.objects.count() - before
        except Exception as error:
            raise CommandError(
                f'Ошибка импорта {self.filename}: {error}'
            ) from error
        self.stdout.write(self.style.SUCCESS(
            f'{self.model._meta.verbose_name_plural}: '
            f'загружено {added}, всего {self.model.objects.count()}'
        ))

    def default_path(self):
        mounted = Path('/data') / self.filename
        return mounted if mounted.is_file() else (
            settings.BASE_DIR.parent / 'data' / self.filename
        )
