from django.shortcuts import get_object_or_404, redirect

from rest_framework import generics, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action

from django.urls import reverse
from django.db.models import Sum
from django.http import HttpResponse

from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .filters import RecipeFilter

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
    RecipeIngredient,
)
from users.models import Subscription, User

from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
)


class SubscriptionPagination(PageNumberPagination):
    """Пагинация списка подписок."""

    page_size = 6
    page_size_query_param = 'limit'


class SubscriptionListView(generics.ListAPIView):
    """Получение списка подписок текущего пользователя."""

    serializer_class = SubscriptionUserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(
            subscribers__user=self.request.user
        ).order_by('id')


class SubscribeView(APIView):
    """Подписка на автора и отмена подписки."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, user_id):
        author = get_object_or_404(
            User,
            id=user_id,
        )

        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Subscription.objects.filter(
            user=request.user,
            author=author,
        ).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Subscription.objects.create(
            user=request.user,
            author=author,
        )

        serializer = SubscriptionUserSerializer(
            author,
            context={'request': request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, user_id):
        author = get_object_or_404(
            User,
            id=user_id,
        )

        subscription = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).first()

        if subscription is None:
            return Response(
                {'errors': 'Вы не подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class AvatarView(APIView):
    """Загрузка, замена и удаление аватара."""

    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        user = request.user

        if user.avatar:
            user.avatar.delete(save=False)

        user.avatar = None
        user.save(update_fields=['avatar'])

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр ингредиентов и поиск по названию."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()

        name = self.request.query_params.get('name')

        if name:
            queryset = queryset.filter(
                name__istartswith=name
            )

        return queryset


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Редактировать и удалять рецепт может только его автор."""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        return (
            request.user.is_authenticated
            and obj.author == request.user
        )


class RecipeViewSet(viewsets.ModelViewSet):
    """Просмотр, создание, редактирование и удаление рецептов."""

    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related(
        'tags',
        'recipe_ingredients__ingredient',
    )

    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return super().get_queryset().distinct()

    http_method_names = (
        'get',
        'post',
        'patch',
        'delete',
        'head',
        'options',
    )

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer

        return RecipeReadSerializer

    @staticmethod
    def manage_recipe_relation(request, recipe, model, delete=False):
        """Добавление или удаление рецепта из коллекции."""

        relation = model.objects.filter(
            user=request.user,
            recipe=recipe,
        )

        if delete:
            if not relation.exists():
                return Response(
                    {'errors': 'Рецепта нет в списке.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            relation.delete()

            return Response(
                status=status.HTTP_204_NO_CONTENT,
            )

        if relation.exists():
            return Response(
                {'errors': 'Рецепт уже добавлен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        model.objects.create(
            user=request.user,
            recipe=recipe,
        )

        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное и удаление из него."""

        recipe = self.get_object()

        return self.manage_recipe_relation(
            request,
            recipe,
            Favorite,
            delete=request.method == 'DELETE',
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок и удаление."""

        recipe = self.get_object()

        return self.manage_recipe_relation(
            request,
            recipe,
            ShoppingCart,
            delete=request.method == 'DELETE',
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок пользователя."""

        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_carts__user=request.user
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        shopping_list = [
            'Список покупок Foodgram',
            '========================',
            '',
        ]

        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['total_amount']

            shopping_list.append(
                f'{name} — {amount} {unit}'
            )

        content = '\n'.join(shopping_list)

        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )

        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""

        recipe = self.get_object()

        short_url = reverse(
            'recipe-short-redirect',
            kwargs={'short_code': recipe.short_code},
        )

        return Response(
            {
                'short-link': request.build_absolute_uri(short_url),
            },
            status=status.HTTP_200_OK,
        )


def recipe_short_redirect(request, short_code):
    """Перенаправление по короткой ссылке на страницу рецепта."""

    recipe = get_object_or_404(
        Recipe,
        short_code=short_code,
    )

    return redirect(
        f'/recipes/{recipe.id}/'
    )
