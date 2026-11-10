from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def recipe_short_redirect(request, recipe_id):
    """Перенаправить короткую ссылку на страницу рецепта."""
    if not Recipe.objects.filter(pk=recipe_id).exists():
        raise Http404('Рецепт не найден.')
    return redirect(f'/recipes/{recipe_id}/')
