from django.db.models import Sum
from django.utils import timezone

from recipes.models import Recipe, RecipeIngredient


def build_shopping_list(user):
    """Сформировать текст списка продуктов и рецептов пользователя."""
    products = (
        RecipeIngredient.objects.filter(
            recipe__shoppingcart_entries__user=user,
        )
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    recipes = (
        Recipe.objects.filter(shoppingcart_entries__user=user)
        .select_related('author')
        .order_by('name')
    )
    return '\n'.join([
        'Список покупок Foodgram',
        f'Дата составления: {timezone.localdate():%d.%m.%Y}',
        '',
        'Продукты:',
        *(
            f'{number}. {product["ingredient__name"].capitalize()} — '
            f'{product["total_amount"]} '
            f'({product["ingredient__measurement_unit"]})'
            for number, product in enumerate(products, start=1)
        ),
        '',
        'Рецепты:',
        *(
            f'{number}. {recipe.name} — @{recipe.author.username}'
            for number, recipe in enumerate(recipes, start=1)
        ),
        '',
    ])
