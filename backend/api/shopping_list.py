from django.utils import timezone

PRODUCT_LINE = '{number}. {name} — {amount} ({unit})'
RECIPE_LINE = '{number}. {name} — @{author} ({tags})'


def build_shopping_list(products, recipes):
    """Сформировать текст списка покупок."""
    return '\n'.join([
        'Список покупок Foodgram',
        f'Дата составления: {timezone.localdate():%d.%m.%Y}',
        '',
        'Продукты:',
        *(
            PRODUCT_LINE.format(
                number=number,
                name=product['ingredient__name'].capitalize(),
                amount=product['total_amount'],
                unit=product['ingredient__measurement_unit'],
            )
            for number, product in enumerate(products, start=1)
        ),
        '',
        'Рецепты:',
        *(
            RECIPE_LINE.format(
                number=number,
                name=recipe.name,
                author=recipe.author.username,
                tags=', '.join(tag.name for tag in recipe.tags.all()),
            )
            for number, recipe in enumerate(recipes, start=1)
        ),
        '',
    ])
