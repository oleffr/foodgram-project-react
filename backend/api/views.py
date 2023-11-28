from django.db.models import Exists, OuterRef, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as d_UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from users.models import User, Subscription
from .permissions import AuthorOrReadOnly
from recipes.models import (Ingredient, Recipe,
                            RecipeIngredient, Tag)
from .serializers import (CreateRecipeSerializer, UserSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer,
                          SubscriptionPresentSerializer,
                          TagSerializer)
from .utils import download_csv


class UserViewSet(d_UserViewSet):
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
        if not Subscription.objects.filter(subscriber=request.user,
                                           author=author).exists():
            raise ValidationError('Такой подписки нет')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @to_subscribe.mapping.delete
    def delete_subscription(self, request, id):
        author = get_object_or_404(User, id=id)
        if not Subscription.objects.filter(subscriber=request.user,
                                           author=author).exists():
            raise ValidationError('Такой подписки нет')
        Subscription.objects.filter(subscriber=request.user,
                                    author=author).delete()

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
            serializer = ShoppingCartSerializer(data={'user': request.user.id,
                                                      'recipe': pk})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        if self.request.user.is_authenticated:
            queryset = ShoppingCartSerializer.Meta.model.objects.filter(
                user=request.user,
                recipe=get_object_or_404(Recipe, pk=pk))
            if not queryset.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif not self.request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @get_shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        if self.request.user.is_authenticated:
            queryset = ShoppingCartSerializer.Meta.model.objects.filter(
                user=request.user,
                recipe=get_object_or_404(Recipe, pk=pk))
            if not queryset.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            queryset.delete()
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    @action(
        detail=True,
        methods=['post'],
        url_path='favorites',
        url_name='favorites',
    )
    def get_favorite(self, request, pk):
        if request.method == 'POST':
            serializer = FavoriteSerializer(data={'user': request.user.id,
                                                  'recipe': pk})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        if self.request.user.is_authenticated:
            queryset = FavoriteSerializer.Meta.model.objects.filter(
                user=request.user,
                recipe=get_object_or_404(Recipe, pk=pk))
            if not queryset.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @get_favorite.mapping.delete
    def delete_favorite(self, request, pk):
        queryset = FavoriteSerializer.Meta.model.objects.filter(
            user=request.user,
            recipe=get_object_or_404(Recipe, pk=pk))
        if not queryset.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        queryset.delete()

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        if not (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit',
            ).annotate(amount=Sum('amount')
                       ).order_by('ingredient__name')
        ).exists():
            raise ValidationError('В списке покупок нет добавленных рецептов')
        response = download_csv(
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit',
            ).annotate(amount=Sum('amount')
                       ).order_by('ingredient__name')
        )
        return response
