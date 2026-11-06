import django_filters

from recipes.models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    """Фильтрация рецептов по автору, тегам и коллекциям."""

    author = django_filters.NumberFilter(
        field_name='author_id',
    )

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
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_favorited(self, queryset, name, value):
        if value != 1:
            return queryset

        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(
            favorites__user=user,
        )

    def filter_shopping_cart(self, queryset, name, value):
        if value != 1:
            return queryset

        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        return queryset.filter(
            shopping_carts__user=user,
        )
