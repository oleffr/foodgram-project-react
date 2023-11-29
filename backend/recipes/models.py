from colorfield.fields import ColorField
from django.core.validators import (MinValueValidator,
                                    MaxValueValidator)
from django.db import models

from backend.backend.constants import (MAX_AMOUNT_CONST,
                                       MAX_COOKING_TIME_CONST,
                                       MIN_AMOUNT_CONST,
                                       MIN_COOKING_TIME_CONST,
                                       USERNAME_FIELD_CONST,)
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=USERNAME_FIELD_CONST,
        verbose_name='Hазвание ингредиента',
        db_index=True,
        blank=False
    )
    measurement_unit = models.CharField(
        max_length=USERNAME_FIELD_CONST,
        verbose_name='Единица измерения ингредиента',
        blank=False
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_and_unit',
            ),
        ]


class Tag(models.Model):
    name = models.CharField(max_length=USERNAME_FIELD_CONST,
                            verbose_name='Hазвание тега',
                            unique=True, db_index=True)
    color = ColorField(default='#FF0000', max_length=7,
                       verbose_name='цвет', unique=True)
    slug = models.SlugField(
        max_length=USERNAME_FIELD_CONST,
        verbose_name='slug',
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
        blank=False
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        blank=False
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение',
        blank=False
    )
    name = models.CharField(
        max_length=USERNAME_FIELD_CONST,
        verbose_name='Hазвание',
        db_index=True,
        blank=False
    )
    text = models.TextField(verbose_name='описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(MIN_COOKING_TIME_CONST),
                    MaxValueValidator(MAX_COOKING_TIME_CONST)
                    ],)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
        db_index=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date', ]


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=[MinValueValidator(MIN_AMOUNT_CONST),
                    MaxValueValidator(MAX_AMOUNT_CONST)
                    ],)

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        constraints = (
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            ),
        )


class ShoppingCartFavorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_recipe_%(class)s'),
        ]
        abstract = True


class ShoppingCart(ShoppingCartFavorite):
    class Meta(ShoppingCartFavorite.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'


class Favorite(ShoppingCartFavorite):
    class Meta(ShoppingCartFavorite.Meta):
        verbose_name = 'Избранное'
