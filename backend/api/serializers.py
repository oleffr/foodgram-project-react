from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import Subscription, User

from backend.constants import (MAX_AMOUNT_CONST,
                               MAX_COOKING_TIME_CONST,
                               MIN_AMOUNT_CONST,
                               MIN_COOKING_TIME_CONST
                               )
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class UserSerializer(UserSerializer):
    is_subscribed = serializers.BooleanField(default=False)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed')
        read_only_fields = ('id',)


class CreateUserSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'password')
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ('id',)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('author',
                  'subscriber')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('author', 'subscriber'),
                message='Такая подписка уже оформлена'
            )
        ]

    def to_representation(self, instance):
        return SubscriptionPresentSerializer(
            instance.author,
            context=self.context
        ).data

    def validate(self, data):
        if data['subscriber'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        return data


class SubscriptionPresentSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, object):
        return object.recipes.count()

    def get_recipes(self, object):
        author_recipes = self.recipes_limit(object.recipes.all())
        return RecipePresentSerializer(
            author_recipes, many=True
        ).data

    def recipes_limit(self, queryset):
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit:
            return queryset[:int(limit)]
        return queryset


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user',
                  'recipe')
        validators = [UniqueTogetherValidator(
                      queryset=Favorite.objects.all(),
                      fields=('user', 'recipe'),
                      message='Рецепт уже добавлен в избраное')
                      ]

    def to_representation(self, instance):
        return RecipePresentSerializer(
            instance.recipe
        ).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id',
                  'color',
                  'name',
                  'slug')


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [UniqueTogetherValidator(
                      queryset=ShoppingCart.objects.all(),
                      fields=('user', 'recipe'),
                      message='Рецепт уже добавлен в список покупок')
                      ]

    def to_representation(self, instance):
        return RecipePresentSerializer(instance.recipe).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id',
                  'name',
                  'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id',
                  'name',
                  'measurement_unit',
                  'amount')


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate(self, data):
        if not (MIN_AMOUNT_CONST <= data['amount'] <= MAX_AMOUNT_CONST):
            raise serializers.ValidationError(
                'Значение количества ингредиента должно'
                f'лежать в диапазоне от {MIN_AMOUNT_CONST}'
                f'до {MAX_AMOUNT_CONST}')
        return data


class RecipePresentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'image',
                  'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipeingredient_set')
    is_in_shopping_cart = serializers.BooleanField(default=False)
    is_favorited = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'name',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'image',
                  'text',
                  'cooking_time')


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateRecipeIngredientSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = ('id',
                  'ingredients',
                  'tags',
                  'image',
                  'name',
                  'text',
                  'cooking_time',
                  'author')

    def validate_cooking_time(self, data):
        if not (MIN_COOKING_TIME_CONST <= data['cooking_time']
                <= MAX_COOKING_TIME_CONST):
            raise serializers.ValidationError(
                'Значение времени приготовления должно'
                f'лежать в диапазоне от {MIN_COOKING_TIME_CONST}'
                f'до {MAX_COOKING_TIME_CONST}')
        return data

    def make_ingredients_list(self, array_of_ingredients, recipe):
        recipe.ingredients.clear()
        ingredients_list = []
        for ingredient_data in array_of_ingredients:
            ingredients_list.append(
                recipe.ingredients.through(
                    recipe=recipe,
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
            )
        recipe.ingredients.through.objects.bulk_create(ingredients_list)

    def validate_ingredients(self, ingredients):
        array_of_ingredients = []
        for ingredient in ingredients:
            array_of_ingredients.append(ingredient.get('id'))
        if len(array_of_ingredients) != len(set(array_of_ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться')
        if not array_of_ingredients:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один ингридиент')
        return ingredients

    @transaction.atomic
    def create(self, validated_data):
        val_data = validated_data
        validated_tags_data = val_data.pop('tags')
        validated_array_of_ingredients = val_data.pop('ingredients')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(validated_tags_data)
        self.make_ingredients_list(validated_array_of_ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        val_data = validated_data
        try:
            validated_tags_data = val_data.pop('tags')
            array_of_ingredients = val_data.pop('ingredients')
            instance.tags.set(validated_tags_data)
            self.make_ingredients_list(array_of_ingredients, instance)
            return super().update(instance, validated_data)
        except KeyError:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один тэг и ингридиент')

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не могут повторяться')
        if not tags:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один тэг')
        return tags

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Ингредиенты не должны быть без картинки')
        return image

    def to_representation(self, recipe):
        return RecipeSerializer(recipe).data
