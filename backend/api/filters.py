from core.services import maybe_incorrect_layout
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class RecipeFilterSet(filters.FilterSet):
    author = filters.NumberFilter(field_name='author')
    tags = filters.MultipleChoiceFilter(
        field_name='tags__slug', conjoined=False
        )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
        )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            queryset = queryset.filter(in_carts__user=self.request.user)
        else:
            queryset = queryset.exclude(in_carts__user=self.request.user)

        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value:
            queryset = queryset.filter(in_favorites__user=self.request.user)
        else:
            queryset = queryset.exclude(in_favorites__user=self.request.user)

        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method="filter_name")

    class Meta:
        model = Ingredient
        fields = ("name",)

    def filter_name(self, queryset, name, value):
        if value:
            value = maybe_incorrect_layout(value)
            # queryset = queryset.filter(name__icontains=value)
            queryset = queryset.filter(name__istartswith=value)
        return queryset
