from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
)
from .user_models import Subscription, User


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'Наличие рецептов'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (('yes', 'Есть'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = 'Наличие подписок'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (('yes', 'Есть'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscriptions__isnull=True)
        return queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return (('yes', 'Есть'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                author_subscriptions__isnull=False,
            ).distinct()
        if self.value() == 'no':
            return queryset.filter(author_subscriptions__isnull=True)
        return queryset


class HasIngredientRecipesFilter(admin.SimpleListFilter):
    title = 'Используется в рецептах'
    parameter_name = 'in_recipes'

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_time', 'author', 'favorites_count',
        'products_display', 'tags_display', 'image_display',
    )
    search_fields = (
        'name', 'author__username', 'author__email',
        'tags__name', 'ingredients__name',
    )
    list_filter = ('tags', 'author')
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('author')
            .prefetch_related('recipe_ingredients__ingredient', 'tags')
            .annotate(
                favorite_total=Count('favorite_entries', distinct=True),
            )
        )

    @admin.display(description='В избранном', ordering='favorite_total')
    def favorites_count(self, recipe):
        return recipe.favorite_total

    @mark_safe
    @admin.display(description='Продукты')
    def products_display(self, recipe):
        return format_html_join(
            '<br>', '{} — {} {}',
            (
                (entry.ingredient.name, entry.amount,
                 entry.ingredient.measurement_unit)
                for entry in recipe.recipe_ingredients.all()
            ),
        )

    @admin.display(description='Теги')
    def tags_display(self, recipe):
        return ', '.join(tag.name for tag in recipe.tags.all())

    @mark_safe
    @admin.display(description='Картинка')
    def image_display(self, recipe):
        if not recipe.image:
            return '—'
        return format_html(
            '<img src="{}" width="70" height="70" '
            'style="object-fit:cover" alt="{}">',
            recipe.image.url, recipe.name,
        )


class RecipeCountAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipe_total=Count('recipes', distinct=True),
        )

    @admin.display(description='Рецептов', ordering='recipe_total')
    def recipes_count(self, item):
        return item.recipe_total


@admin.register(Ingredient)
class IngredientAdmin(RecipeCountAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name',)
    list_filter = ('measurement_unit', HasIngredientRecipesFilter)


@admin.register(Tag)
class TagAdmin(RecipeCountAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Favorite, ShoppingCart)
class RecipeCollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_display',
        'recipes_count', 'subscriptions_count', 'subscribers_count',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', HasRecipesFilter,
        HasSubscriptionsFilter, HasSubscribersFilter,
    )
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('avatar',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipe_total=Count('recipes', distinct=True),
            subscription_total=Count('subscriptions', distinct=True),
            subscriber_total=Count('author_subscriptions', distinct=True),
        )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return user.get_full_name()

    @mark_safe
    @admin.display(description='Аватар')
    def avatar_display(self, user):
        if not user.avatar:
            return '—'
        return format_html(
            '<img src="{}" width="50" height="50" '
            'style="object-fit:cover" alt="Аватар">', user.avatar.url,
        )

    @admin.display(description='Рецептов', ordering='recipe_total')
    def recipes_count(self, user):
        return user.recipe_total

    @admin.display(description='Подписок', ordering='subscription_total')
    def subscriptions_count(self, user):
        return user.subscription_total

    @admin.display(description='Подписчиков', ordering='subscriber_total')
    def subscribers_count(self, user):
        return user.subscriber_total


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')
