from recipes.models import Ingredient

from .import_base import ImportJsonCommand


class Command(ImportJsonCommand):
    help = 'Загрузить продукты из JSON'
    model = Ingredient
    filename = 'ingredients.json'
