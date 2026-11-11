from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import (
    MAX_INGREDIENT_NAME_LENGTH,
    MAX_MEASUREMENT_UNIT_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_TAG_LENGTH,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)


class User(AbstractUser):
    """Пользователь Foodgram."""

    username = models.CharField(
        'Ник',
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=settings.USERNAME_REGEX,
            ),
        ],
    )

    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
    )

    first_name = models.CharField(
        'Имя',
        max_length=150,
    )

    last_name = models.CharField(
        'Фамилия',
        max_length=150,
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписка пользователя на автора."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author_subscriptions',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author_subscription',
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            ),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


class Tag(models.Model):
    """Тег для классификации рецептов."""

    name = models.CharField(
        'Название',
        max_length=MAX_TAG_LENGTH,
        unique=True,
    )

    slug = models.SlugField(
        'Идентификатор',
        max_length=MAX_TAG_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Продукт с единицей измерения."""

    name = models.CharField(
        'Название',
        max_length=MAX_INGREDIENT_NAME_LENGTH,
    )

    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)

        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_measurement',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Рецепт пользователя."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )

    name = models.CharField(
        'Название',
        max_length=MAX_RECIPE_NAME_LENGTH,
    )

    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/',
    )

    text = models.TextField(
        'Описание',
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Продукты',
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )

    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )

    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Количество продукта в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Продукт',
    )

    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_AMOUNT)],
    )

    class Meta:
        verbose_name = 'Продукт рецепта'
        verbose_name_plural = 'Продукты рецептов'

        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        ]

    def __str__(self):
        return f'{self.ingredient} — {self.amount}'


class RecipeCollection(models.Model):
    """Базовая модель коллекции рецептов пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s_user_recipe',
            ),
        ]

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class Favorite(RecipeCollection):
    """Избранный рецепт."""

    class Meta(RecipeCollection.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(RecipeCollection):
    """Рецепт в списке покупок."""

    class Meta(RecipeCollection.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
