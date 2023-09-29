from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Стандартный пагинатор с определением атрибута."""
    page_size = 10
    page_size_query_param = "limit"
