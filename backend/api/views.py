from django.db.models import Exists, OuterRef, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import AuthorOrReadOnly
from api.serializers import (CreateRecipeSerializer, FavoriteSerializer,
                             IngredientSerializer, RecipeSerializer,
                             ShoppingCartSerializer,
                             SubscriptionPresentSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserSerializer)
from api.utils import download_csv
from recipes.models import (Favorite,
                            Ingredient,
                            Recipe,
                            RecipeIngredient,
                            ShoppingCart,
                            Tag)
from users.models import Subscription, User


class UserViewSet(UserViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_authenticated:
            return queryset.annotate(
                is_subscribed=Exists(
                    user.subscriber.filter(author=OuterRef('pk'))
                ))
        return queryset

    def get_serializer_class(self):
        if self.action == 'to_subscribe':
            return SubscriptionSerializer
        if self.action == 'get_subscription_list':
            return SubscriptionPresentSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        url_name='subscribe',
    )
    def to_subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = self.get_serializer(data={
                'subscriber': request.user.id,
                'author': author.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )

    @to_subscribe.mapping.delete
    def delete_subscription(self, request, id):
        author = get_object_or_404(User, id=id)
        subscription = get_object_or_404(Subscription.objects.filter(
                                         subscriber=request.user,
                                         author=author))
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        url_name='subscriptions'
    )
    def get_subscription_list(self, request):
        authors = User.objects.filter(author__subscriber=request.user)
        return self.get_paginated_response(self.get_serializer(
            self.paginate_queryset(queryset=authors), many=True).data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    search_fields = ['name']
    pagination_class = None
    filterset_class = IngredientFilter
    permission_classes = (AllowAny, )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny, )


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, AuthorOrReadOnly
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return (Recipe.objects.all().select_related('author')
                    .annotate(is_favorited=Exists(
                        Favorite.objects.filter(recipe=OuterRef('pk'))
                        .select_related('user')
                    ))
                    .annotate(is_in_shopping_cart=Exists(ShoppingCart.objects
                                                         .filter(
                                                             recipe=OuterRef(
                                                                 'pk'))
                                                         .select_related(
                                                             'user')
                                                         ))
                    .prefetch_related('tags', 'ingredients')
                    )
        return (Recipe.objects.all().select_related('author')
                .prefetch_related('tags', 'ingredients'))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return CreateRecipeSerializer

    @action(
        detail=True,
        methods=['post'],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def get_shopping_cart(self, request, pk):
        if request.method == 'POST':
            data = {'user': request.user.id, 'recipe': pk}
            serializer = ShoppingCartSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )

    @get_shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        queryset = ShoppingCartSerializer.Meta.model.objects.filter(
            user=request.user,
            recipe=get_object_or_404(Recipe, pk=pk))
        count, _ = queryset.delete()
        if not count:
            raise ValidationError('Рецепт не в корзине')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='favorite',
        url_name='favorite',
    )
    def get_favorite(self, request, pk):
        if request.method == 'POST':
            data = {'user': request.user.id, 'recipe': pk}
            serializer = FavoriteSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )

    @get_favorite.mapping.delete
    def delete_favorite(self, request, pk):
        queryset = FavoriteSerializer.Meta.model.objects.filter(
            user=request.user,
            recipe=get_object_or_404(Recipe, pk=pk))
        count, _ = queryset.delete()
        if not count:
            raise ValidationError('Рецепт не в избранном')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__user=user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit',
            ).annotate(ingredient_value=Sum('amount')
                       ).order_by('ingredient__name')
        )
        if not ingredients.exists():
            raise ValidationError('Корзина пуста')
        response = download_csv(ingredients)
        return response
