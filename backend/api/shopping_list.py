from django.utils import timezone

PRODUCT_LINE = '{number}. {name} — {amount} ({unit})'
RECIPE_LINE = '{number}. {name} — @{author} ({tags})'


def build_shopping_list(products, recipes):
    """Сформировать текст списка покупок."""
    return '\n'.join([
        'Список покупок Foodgram',
        (
            'Дата составления: {} {} {}'.format(
                timezone.localdate().day,
                (
                    'января', 'февраля', 'марта', 'апреля',
                    'мая', 'июня', 'июля', 'августа',
                    'сентября', 'октября', 'ноября', 'декабря',
                )[timezone.localdate().month - 1],
                timezone.localdate().year,
            )
        ),
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
