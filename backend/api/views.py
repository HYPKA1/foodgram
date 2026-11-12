from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
    Subscription, Tag, User,
)

from .filters import IngredientFilter, RecipeFilter
from .pagination import FoodgramPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, IngredientSerializer, RecipeReadSerializer,
    RecipeShortSerializer, RecipeWriteSerializer,
    SubscriptionUserSerializer, TagSerializer,
)
from .shopping_list import build_shopping_list


class UserViewSet(DjoserUserViewSet):
    """Пользователи, подписки и аватары."""

    queryset = User.objects.all()

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            author_subscriptions__user=request.user,
        )
        paginator = FoodgramPagination()
        page = paginator.paginate_queryset(authors, request, view=self)
        return paginator.get_paginated_response(
            SubscriptionUserSerializer(
                page, many=True, context={'request': request},
            ).data
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        if request.method == 'DELETE':
            get_object_or_404(
                Subscription, user=request.user, author_id=id,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = self.get_object()
        if author == request.user:
            raise ValidationError('Нельзя подписаться на себя.')
        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author,
        )
        if not created:
            raise ValidationError(
                f'Подписка уже существует: {author.username}.'
            )
        return Response(
            SubscriptionUserSerializer(
                author, context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False, methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        if request.method == 'DELETE':
            if request.user.avatar:
                request.user.avatar.delete(save=False)
            request.user.avatar = None
            request.user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            request.user, data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Продукты с поиском."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты, избранное и список покупок."""

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'recipe_ingredients__ingredient',
    ).distinct()
    permission_classes = (
        IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def manage_recipe_relation(request, pk, model):
        """Добавить или удалить рецепт."""
        if request.method == 'DELETE':
            get_object_or_404(
                model, user=request.user, recipe_id=pk,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model.objects.get_or_create(
            user=request.user, recipe=recipe,
        )
        if not created:
            raise ValidationError(
                f'Рецепт «{recipe.name}» уже в '
                f'«{model._meta.verbose_name}».'
            )
        return Response(
            RecipeShortSerializer(recipe).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self.manage_recipe_relation(
            request, pk, Favorite,
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self.manage_recipe_relation(
            request, pk, ShoppingCart,
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        products = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user,
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        recipes = (
            Recipe.objects.filter(shoppingcarts__user=request.user)
            .select_related('author')
            .prefetch_related('tags')
            .order_by('name')
        )
        return FileResponse(
            build_shopping_list(products, recipes),
            as_attachment=True,
            filename='shopping_list.txt',
            content_type='text/plain',
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise Http404(f'Рецепт с ID {pk} не найден.')
        return Response({
            'short-link': request.build_absolute_uri(
                reverse('recipe-short-redirect', args=[pk]),
            ),
        })
