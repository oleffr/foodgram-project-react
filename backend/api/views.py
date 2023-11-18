import csv

from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            SaleList, Tag)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from users.models import CustomUser, Subscription

from .filters import IngredientFilter, RecipeFilter
from .permissions import AuthorOrAdminOrReadOnly
from .serializers import (CreateRecipeSerializer, UserSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer,
                          SubscriptionPresentSerializer,
                          TagSerializer)


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
        methods=['post', 'delete'],
        url_path='subscribe',
        url_name='subscribe',
    )
    def to_subscribe(self, request, id):
        author = get_object_or_404(CustomUser, id=id)
        if request.method == 'POST':
            data = {'subscriber': request.user.id, 'author': author.id}
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        subscription = Subscription.objects.filter(subscriber=request.user,
                                                   author=author)
        if not subscription.exists():
            raise ValidationError('Такой подписки нет')
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        url_name='subscriptions'
    )
    def get_subscription_list(self, request):
        authors = CustomUser.objects.filter(author__subscriber=request.user)
        result_pages = self.paginate_queryset(
            queryset=authors
        )
        serializer = self.get_serializer(result_pages, many=True)
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny, )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    search_fields = ['name']
    pagination_class = None
    filterset_class = IngredientFilter
    permission_classes = (AllowAny, )


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, AuthorOrAdminOrReadOnly
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
                    .annotate(is_in_shopping_cart=Exists(SaleList.objects
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
        methods=['post', 'delete'],
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
        model = ShoppingCartSerializer.Meta.model
        if self.request.user.is_authenticated:
            queryset = model.objects.filter(user=request.user,
                                            recipe=get_object_or_404(
                                                Recipe, pk=pk))
            if not queryset.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            queryset.delete()
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
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
        model = FavoriteSerializer.Meta.model
        if self.request.user.is_authenticated:
            queryset = model.objects.filter(user=request.user,
                                            recipe=get_object_or_404(
                                                Recipe, pk=pk))
            if not queryset.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            queryset.delete()
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients_cart = (
            RecipeIngredient.objects.filter(
                recipe__sale_cart__user=request.user
            ).values(
                'ingredient__name',
                'ingredient__measurement_unit',
            ).annotate(ingredient_value=Sum('amount')
                       ).order_by('ingredient__name')
        )
        if not ingredients_cart.exists():
            raise ValidationError({'errors': 'Корзина пуста'})
        response = HttpResponse(content_type="text/csv",
                                headers={'Content-Disposition':
                                         'attachment;filename="shop_list.csv"'
                                         },
                                )
        writer = csv.DictWriter(response,
                                fieldnames=ingredients_cart.first().keys())
        writer.writeheader()
        writer.writerows(ingredients_cart)
        return response
