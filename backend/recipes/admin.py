from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    """Редактирование ингредиентов внутри рецепта."""

    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Администрирование рецептов."""

    list_display = (
        'id',
        'name',
        'author',
        'pub_date',
        'favorites_count',
    )

    search_fields = (
        'name',
        'author__username',
        'author__email',
    )

    list_filter = ('tags',)

    inlines = (RecipeIngredientInline,)

    @admin.display(description='Добавлений в избранное')
    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Администрирование ингредиентов."""

    list_display = (
        'id',
        'name',
        'measurement_unit',
    )

    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Администрирование тегов."""

    list_display = (
        'id',
        'name',
        'slug',
    )

    search_fields = (
        'name',
        'slug',
    )


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Управление ингредиентами рецептов."""

    list_display = (
        'id',
        'recipe',
        'ingredient',
        'amount',
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Управление избранными рецептами."""

    list_display = (
        'id',
        'user',
        'recipe',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Управление списками покупок."""

    list_display = (
        'id',
        'user',
        'recipe',
    )
