from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return obj.subscribers.filter(
            user=request.user
        ).exists()


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Регистрация нового пользователя."""

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткая информация о рецепте."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionUserSerializer(UserSerializer):
    """Информация об авторе, на которого подписан пользователь."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True,
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        recipes = obj.recipes.all()

        request = self.context.get('request')

        if request:
            recipes_limit = request.query_params.get(
                'recipes_limit'
            )

            if recipes_limit is not None:
                try:
                    limit = int(recipes_limit)
                except ValueError:
                    raise serializers.ValidationError(
                        'recipes_limit должен быть числом.'
                    )

                if limit < 0:
                    raise serializers.ValidationError(
                        'recipes_limit не может быть отрицательным.'
                    )

                recipes = recipes[:limit]

        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class AvatarSerializer(serializers.ModelSerializer):
    """Загрузка аватара пользователя в формате Base64."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Ингредиент с количеством для отображения рецепта."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """Ингредиент с количеством для создания рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    amount = serializers.IntegerField(min_value=1)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Полная информация о рецепте."""

    author = UserSerializer(read_only=True)

    tags = TagSerializer(many=True, read_only=True)

    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )

    is_favorited = serializers.SerializerMethodField()

    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return obj.favorites.filter(
            user=request.user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return obj.shopping_carts.filter(
            user=request.user
        ).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Создание и редактирование рецептов."""

    ingredients = RecipeIngredientWriteSerializer(
        many=True
    )

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )

    image = Base64ImageField()

    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )

        ingredient_ids = [
            item['id'].id for item in value
        ]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег.'
            )

        tag_ids = [tag.id for tag in value]

        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )

        return value

    @staticmethod
    def save_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item['id'],
                    amount=item['amount'],
                )
                for item in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data,
        )

        recipe.tags.set(tags)

        self.save_ingredients(recipe, ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop(
            'ingredients',
            None,
        )

        tags = validated_data.pop(
            'tags',
            None,
        )

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.all().delete()

            self.save_ingredients(
                instance,
                ingredients,
            )

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context,
        ).data
