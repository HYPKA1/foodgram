from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
    Subscription, Tag, User,
)

FILTER_OPTIONS = (('yes', 'Да'), ('no', 'Нет'))


class RelationPresenceFilter(admin.SimpleListFilter):
    """Фильтр наличия связей."""

    relation = None

    def lookups(self, request, model_admin):
        return FILTER_OPTIONS

    def queryset(self, request, queryset):
        if self.value() not in ('yes', 'no'):
            return queryset
        condition = {f'{self.relation}__isnull': self.value() == 'no'}
        return queryset.filter(**condition).distinct()


class HasRecipesFilter(RelationPresenceFilter):
    title = 'Наличие рецептов'
    parameter_name = 'has_recipes'
    relation = 'recipes'


class HasSubscriptionsFilter(RelationPresenceFilter):
    title = 'Наличие подписок'
    parameter_name = 'has_subscriptions'
    relation = 'subscriptions'


class HasSubscribersFilter(RelationPresenceFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'has_subscribers'
    relation = 'author_subscriptions'


class HasIngredientRecipesFilter(RelationPresenceFilter):
    title = 'Используется в рецептах'
    parameter_name = 'in_recipes'
    relation = 'recipes'


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_duration'

    def lookups(self, request, model_admin):
        return (
            ('fast', 'Быстрые (до 20 мин)'),
            ('medium', 'Средние (20–60 мин)'),
            ('slow', 'Долгие (от 60 мин)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lt=20)
        if self.value() == 'medium':
            return queryset.filter(
                cooking_time__gte=20, cooking_time__lt=60
            )
        if self.value() == 'slow':
            return queryset.filter(cooking_time__gte=60)
        return queryset


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'cooking_minutes', 'author', 'favorites_count',
        'products_display', 'tags_display', 'image_display',
    )
    search_fields = (
        'name', 'author__username', 'author__email',
        'tags__name', 'ingredients__name',
    )
    list_filter = ('tags', 'author', CookingTimeFilter)
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('image_display',)

    @admin.display(description='Время (мин)', ordering='cooking_time')
    def cooking_minutes(self, recipe):
        return recipe.cooking_time

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('author')
            .prefetch_related('recipe_ingredients__ingredient', 'tags')
            .annotate(
                favorite_total=Count('favorites', distinct=True),
            )
        )

    @admin.display(
        description='В избранном', ordering='favorite_total',
    )
    def favorites_count(self, recipe):
        return recipe.favorite_total

    @mark_safe
    @admin.display(description='Продукты')
    def products_display(self, recipe):
        return '<br>'.join(
            '{} — {} {}'.format(
                escape(entry.ingredient.name),
                entry.amount,
                escape(entry.ingredient.measurement_unit),
            )
            for entry in recipe.recipe_ingredients.all()
        )

    @mark_safe
    @admin.display(description='Теги')
    def tags_display(self, recipe):
        return '<br>'.join(escape(tag.name) for tag in recipe.tags.all())

    @mark_safe
    @admin.display(description='Картинка')
    def image_display(self, recipe):
        if not recipe.image:
            return '—'
        return (
            '<img src="{}" width="70" height="70" '
            'style="object-fit:cover" alt="{}">'
        ).format(recipe.image.url, escape(recipe.name))


class RecipeCountMixin:
    list_display = ('recipes_count',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipe_total=Count('recipes', distinct=True),
        )

    @admin.display(description='Рецептов', ordering='recipe_total')
    def recipes_count(self, item):
        return item.recipe_total


@admin.register(Ingredient)
class IngredientAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',
                    *RecipeCountMixin.list_display)
    search_fields = ('name',)
    list_filter = ('measurement_unit', HasIngredientRecipesFilter)


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug',
                    *RecipeCountMixin.list_display)
    search_fields = ('name', 'slug')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Favorite, ShoppingCart)
class RecipeCollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')


@admin.register(User)
class FoodgramUserAdmin(RecipeCountMixin, UserAdmin):
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_display',
        *RecipeCountMixin.list_display,
        'subscriptions_count', 'subscribers_count',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', HasRecipesFilter,
        HasSubscriptionsFilter, HasSubscribersFilter,
    )
    ordering = ('username',)
    readonly_fields = ('avatar_display',)
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar', 'avatar_display')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
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
        return (
            '<img src="{}" width="50" height="50" '
            'style="object-fit:cover" alt="Аватар">'
        ).format(escape(user.avatar.url))

    @admin.display(
        description='Подписок', ordering='subscription_total',
    )
    def subscriptions_count(self, user):
        return user.subscription_total

    @admin.display(
        description='Подписчиков', ordering='subscriber_total',
    )
    def subscribers_count(self, user):
        return user.subscriber_total


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')


try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass
