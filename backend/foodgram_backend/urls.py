from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import recipe_short_redirect


urlpatterns = [
    path('admin/', admin.site.urls),

    # Наши API-эндпоинты
    path('api/', include('api.urls')),

    # Djoser: пользователи
    path('api/', include('djoser.urls')),

    # Djoser: авторизация
    path('api/auth/', include('djoser.urls.authtoken')),

    path(
        's/<str:short_code>/',
        recipe_short_redirect,
        name='recipe-short-redirect',
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
