from core.services import create_shoping_list
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http.response import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Carts, Favorites, Ingredient, Recipe, Tag
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_405_METHOD_NOT_ALLOWED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.models import Subscriptions

from api.mixins import AddDelViewMixin
from api.paginators import PageLimitPagination
from api.permissions import AdminOrReadOnly, AuthorStaffOrReadOnly
from api.serializers import (IngredientSerializer, RecipeSerializer,
    RecipeSummarySerializer, TagSerializer,
    UserSubscribeSerializer)
from django_filters import rest_framework as filters
from api.filters import RecipeFilterSet, IngredientFilter

User = get_user_model()

class UserViewSet(DjoserUserViewSet, AddDelViewMixin):
    """Класс представления для пользователей с возможностью подписки."""
    pagination_class = PageLimitPagination
    permission_classes = (DjangoModelPermissions,)
    add_serializer = UserSubscribeSerializer
    link_model = Subscriptions

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id: int | str) -> Response:
        """Создаёт, удаляет связь между пользователями."""

    @subscribe.mapping.post
    def create_subscribe(self, request, id: int | str) -> Response:
        """Создаёт связь подписки между пользователями."""
        return self._create_relation(id, relation_type="subscription")

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id: int | str) -> Response:
        """Удаляет связь подписки между пользователями."""
        return self._delete_relation(Q(author__id=id))

    @action(
        methods=("get",), detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request) -> Response:
        """Получает список подписок пользователя."""
        pages = self.paginate_queryset(
            User.objects.filter(subscribers__user=self.request.user)
        )
        serializer = UserSubscribeSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """Класс представления для тегов рецептов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)

class IngredientViewSet(ReadOnlyModelViewSet):
    """Класс представления для ингредиентов рецептов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = IngredientFilter

# def get_queryset(self):
#     """Запрашивает список ингредиентов c фильтрацией по имени."""
#     name: str = self.request.query_params.get("name")
#     queryset = self.queryset

#     if not name:
#         return queryset

#     name = maybe_incorrect_layout(name)
#     start_queryset = queryset.filter(name__istartswith=name)
#     start_names = (ing.name for ing in start_queryset)
#     contain_queryset = queryset.filter(name__icontains=name).exclude(
#         name__in=start_names)
#     return list(start_queryset) + list(contain_queryset)
class RecipeViewSet(ModelViewSet, AddDelViewMixin):
    """Класс представления для рецептов с возможностью добавления в
    избранное и корзину."""
    queryset = Recipe.objects.select_related("author")
    serializer_class = RecipeSerializer
    permission_classes = (AuthorStaffOrReadOnly,)
    pagination_class = PageLimitPagination
    add_serializer = RecipeSummarySerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilterSet

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk: int | str) -> Response:
        """Добавляет, удалет рецепт в избранное."""

    @favorite.mapping.post
    def recipe_to_favorites(self, request, pk: int | str) -> Response:
        """Добавляет рецепт в избранное."""
        self.link_model = Favorites
        return self._create_relation(pk, relation_type="favorite")

    @favorite.mapping.delete
    def remove_recipe_from_favorites(self, request, pk: int | str) -> Response:
        """Удаляет рецепт из избранного."""
        self.link_model = Favorites
        return self._delete_relation(Q(recipe__id=pk))

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk: int | str) -> Response:
        """Добавляет, удалет рецепт в список покупок."""
        return Response({"detail": "Method not allowed"}, status=HTTP_405_METHOD_NOT_ALLOWED)


    @shopping_cart.mapping.post
    def recipe_to_cart(self, request, pk: int | str) -> Response:
        """Добавляет рецепт в список покупок."""
        self.link_model = Carts
        return self._create_relation(pk, relation_type="cart")

    @shopping_cart.mapping.delete
    def remove_recipe_from_cart(self, request, pk: int | str) -> Response:
        """Удаляет рецепт из списка покупок."""
        self.link_model = Carts
        return self._delete_relation(Q(recipe__id=pk))

    @action(methods=("get",), detail=False)
    def download_shopping_cart(self, request) -> Response:
        """Загружает список покупок пользователя."""
        user = self.request.user
        if not user.carts.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        filename = f"{user.username}_shopping_list.txt"
        shopping_list = create_shoping_list(user)
        response = HttpResponse(
            shopping_list, content_type="text.txt; charset=utf-8")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
