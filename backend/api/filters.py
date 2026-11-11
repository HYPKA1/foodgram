import django_filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(django_filters.FilterSet):
    """Поиск продуктов по началу названия."""

    name = django_filters.CharFilter(
        field_name='name', lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(django_filters.FilterSet):
    """Фильтрация рецептов по автору, тегам и коллекциям."""

    author = django_filters.NumberFilter(field_name='author_id')
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.NumberFilter(
        method='filter_favorited',
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def _filter_collection(self, recipes, enabled, related_name):
        if enabled != 1:
            return recipes
        if not self.request.user.is_authenticated:
            return recipes.none()
        return recipes.filter(**{
            f'{related_name}__user': self.request.user,
        })

    def filter_favorited(self, recipes, name, value):
        return self._filter_collection(recipes, value, 'favorites')

    def filter_shopping_cart(self, recipes, name, value):
        return self._filter_collection(
            recipes, value, 'shoppingcarts',
        )
