from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Пагинация с поддержкой параметров page и limit."""

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100
