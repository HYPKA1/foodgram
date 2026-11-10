from rest_framework.permissions import (
    BasePermission,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS,
)


class UserReadOnlyOrAuthenticated(BasePermission):
    """Просмотр профилей открыт, остальные действия требуют входа."""

    def has_permission(self, request, view):
        return (
            (request.method in SAFE_METHODS and view.action != 'me')
            or request.user.is_authenticated
        )


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """Изменять рецепт может только его автор."""

    def has_object_permission(self, request, view, recipe):
        return (
            request.method in SAFE_METHODS
            or recipe.author_id == request.user.pk
        )
