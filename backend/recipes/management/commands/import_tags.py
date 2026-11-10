from recipes.models import Tag

from .import_base import ImportJsonCommand


class Command(ImportJsonCommand):
    help = 'Загрузить теги из JSON'
    model = Tag
    filename = 'tags.json'
