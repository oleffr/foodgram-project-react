from django_filters import rest_framework as d_filters
from django.shortcuts import get_object_or_404

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class RecipeFilter(d_filters.FilterSet):
    tags = d_filters.filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = d_filters.BooleanFilter(method='get_is_favorited',
                                           field_name='is_favorited')
    in_cart = d_filters.BooleanFilter(
        method='get_in_cart',
        field_name='in_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author',
                  'tags',
                  'is_favorited',
                  'in_cart')

    def get_in_cart(self, queryset, id, value):
        user = get_object_or_404(User, id=id)
        if value:
            return queryset.filter(shopping_cart__user=user)
        return queryset

    def get_is_favorited(self, queryset, id, value):
        user = get_object_or_404(User, id=id)
        if value:
            return queryset.filter(favoriting__user=user)
        return queryset


class IngredientFilter(d_filters.FilterSet):
    name = d_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', )
