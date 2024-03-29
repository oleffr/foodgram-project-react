from django_filters import rest_framework as d_filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(d_filters.FilterSet):
    tags = d_filters.filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = d_filters.BooleanFilter(method='get_is_favorited',
                                           field_name='is_favorited')
    is_in_shopping_cart = d_filters.BooleanFilter(
        method='get_in_cart',
        field_name='is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author',
                  'tags',
                  'is_favorited',
                  'is_in_shopping_cart')

    def get_in_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shoppingcart__user=self.request.user)
        return queryset

    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset


class IngredientFilter(d_filters.FilterSet):
    name = d_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', )
