from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            SaleList, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import CustomUser, Subscription


class CustomUserSerializer(UserSerializer):
    """Сериализация для отображения пользователей"""
    is_subscribed = serializers.BooleanField(default=False)

    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')
        read_only_fields = ('id',)


class CreateCustomUserSerializer(UserCreateSerializer):
    """Сериализация для создания пользователей"""
    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ('id',)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('author', 'subscriber')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('author', 'subscriber'),
                message='Подписка на этого автора уже есть'
            )
        ]

    def validate(self, data):
        if data['subscriber'] == data['author']:
            raise serializers.ValidationError(
                'Подписка на cамого себя не имеет смысла'
            )
        return data

    def to_representation(self, instance):
        return SubscriptionShowSerializer(
            instance.author,
            context=self.context
        ).data


class SubscriptionShowSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )

    def recipes_limit(self, queryset):
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit:
            return queryset[:int(limit)]
        return queryset

    def get_recipes(self, object):
        author_recipes = self.recipes_limit(object.recipes.all())
        return RecipeShortSerializer(
            author_recipes, many=True
        ).data

    def get_recipes_count(self, object):
        return object.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'color', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source='recipeingredient_set')
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'name',
                  'ingredients', 'is_favorited', 'is_in_shopping_cart',
                  'image', 'text', 'cooking_time')


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateRecipeIngredientSerializer(many=True)
    image = Base64ImageField(use_url=True, max_length=None)
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags',
                  'image', 'name', 'text', 'cooking_time', 'author')
    
    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Ингредиенты не должны быть без картинки'
            )
        return image

    def validate_ingredients(self, ingredients):
        ingredients_data = [
            ingredient.get('id') for ingredient in ingredients]
        if len(ingredients_data) != len(set(ingredients_data)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )
        if len(ingredients_data) == 0:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один ингридиент')
        return ingredients

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторяться')
        if len(tags) == 0:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один тэг')
        return tags

    def _add_ingredients(self, ingredients_data, recipe):
        recipe.ingredients.clear()
        ingredients_list = []
        for ingredient_data in ingredients_data:
            ingredients_list.append(
                recipe.ingredients.through(
                    recipe=recipe,
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
            )
        recipe.ingredients.through.objects.bulk_create(ingredients_list)

    @transaction.atomic
    def create(self, validated_data):
        val_data = validated_data
        validated_tags_data = val_data.pop('tags')
        validated_ingredients_data = val_data.pop('ingredients')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(validated_tags_data)
        self._add_ingredients(validated_ingredients_data, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        val_data = validated_data
        try:
            validated_tags_data = val_data.pop('tags')
            ingredients_data = val_data.pop('ingredients')
            instance.tags.set(validated_tags_data)
            self._add_ingredients(ingredients_data, instance)
            return super().update(instance, validated_data)
        except KeyError:
            raise serializers.ValidationError(
                'У рецепта должен быть хотя бы один тэг и ингридиент')

    def to_representation(self, recipe):
        return RecipeSerializer(recipe).data


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избраном'
            )
        ]

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe
        ).data


class SaleListSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all())

    class Meta:
        model = SaleList
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=SaleList.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке'
            )
        ]

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe
        ).data