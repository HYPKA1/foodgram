from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
)


class IsAuthenticatedForMeOrReadOnly(BasePermission):
    """Права доступа к профилям пользователей."""

    def has_permission(self, request, view):
        if view.action == 'me':
            return request.user.is_authenticated

        if request.method in SAFE_METHODS:
            return True

        return request.user.is_authenticated
