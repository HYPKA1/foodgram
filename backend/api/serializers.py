from collections import Counter

from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MIN_AMOUNT, MIN_COOKING_TIME
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
    Tag, User,
)


def validate_unique_items(items, get_id, item_name):
    """Проверить набор и выявить повторы."""
    if not items:
        raise serializers.ValidationError(
            f'Добавьте хотя бы один {item_name}.'
        )
    counts = Counter(map(get_id, items))
    duplicates = [pk for pk, count in counts.items() if count > 1]
    if duplicates:
        raise serializers.ValidationError(
            f'Повторяющиеся {item_name}: {duplicates}.'
        )
    return items


class UserSerializer(DjoserUserSerializer):
    """Данные пользователя и подписка."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = tuple(dict.fromkeys((
            *DjoserUserSerializer.Meta.fields,
            'avatar', 'is_subscribed',
        )))
        read_only_fields = fields

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and author.author_subscriptions.filter(user=request.user).exists()
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткое представление рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionUserSerializer(UserSerializer):
    """Автор и его рецепты."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True,
    )

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, author):
        request = self.context.get('request')
        recipes = author.recipes.all()
        if request and request.GET.get('recipes_limit') is not None:
            try:
                limit = int(request.GET['recipes_limit'])
            except (ValueError, TypeError) as error:
                raise serializers.ValidationError(
                    {'recipes_limit': 'Укажите целое число.'}
                ) from error
            if limit < 0:
                raise serializers.ValidationError(
                    {'recipes_limit': 'Число меньше нуля.'}
                )
            recipes = recipes[:limit]
        return RecipeShortSerializer(recipes, many=True).data


class AvatarSerializer(serializers.ModelSerializer):
    """Загрузка и замена аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Продукт и единица измерения."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Тег рецепта."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Количество продукта в рецепте."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True,
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Продукт для записи рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Рецепт для чтения."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients', many=True, read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = fields

    def _is_in_collection(self, recipe, model):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and model.objects.filter(
                user=request.user, recipe=recipe,
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self._is_in_collection(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._is_in_collection(recipe, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Создание и редактирование рецепта."""

    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time',
        )

    def validate_ingredients(self, ingredients):
        return validate_unique_items(
            ingredients, lambda item: item['id'].pk, 'продукт',
        )

    def validate_tags(self, tags):
        return validate_unique_items(
            tags, lambda tag: tag.pk, 'тег',
        )

    @staticmethod
    def save_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount'],
            )
            for item in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def validate(self, attrs):
        """Сохранить продукты при частичном обновлении."""
        if self.instance is not None and 'ingredients' not in attrs:
            attrs['ingredients'] = [
                {'id': entry.ingredient, 'amount': entry.amount}
                for entry in self.instance.recipe_ingredients.all()
            ]
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.recipe_ingredients.all().delete()
        self.save_ingredients(instance, validated_data.pop('ingredients'))
        return super().update(instance, validated_data)

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data
