from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AvatarView,
    IngredientViewSet,
    RecipeViewSet,
    SubscribeView,
    SubscriptionListView,
    TagViewSet,
)


router = DefaultRouter()

router.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredients',
)

router.register(
    'tags',
    TagViewSet,
    basename='tags',
)

router.register(
    'recipes',
    RecipeViewSet,
    basename='recipes',
)

urlpatterns = [
    path(
        'users/subscriptions/',
        SubscriptionListView.as_view(),
        name='subscriptions',
    ),
    path(
        'users/<int:user_id>/subscribe/',
        SubscribeView.as_view(),
        name='subscribe',
    ),
    path(
        'users/me/avatar/',
        AvatarView.as_view(),
        name='user-avatar',
    ),
    path('', include(router.urls)),
]
