from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """Изменять рецепт может только его автор."""

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, recipe):
        return (
            request.method in SAFE_METHODS
            or recipe.author == request.user
        )
