from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from backend.settings import FIELD_NUM_1
from users.models import CustomUser


class Tag(models.Model):
    name = models.CharField(max_length=FIELD_NUM_1, verbose_name='Hазвание',
                            unique=True, db_index=True)
    color = ColorField(default='#FF0000', max_length=7,
                       verbose_name='цвет', unique=True)
    slug = models.SlugField(
        max_length=FIELD_NUM_1,
        verbose_name='slug',
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=FIELD_NUM_1,
        verbose_name='Hазвание',
        db_index=True,
        blank=False
    )
    measurement_unit = models.CharField(
        max_length=FIELD_NUM_1,
        verbose_name='Единица измерения',
        blank=False
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


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
        max_length=FIELD_NUM_1,
        verbose_name='Hазвание',
        db_index=True,
        blank=False
    )
    text = models.TextField(verbose_name='описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(1)],)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        db_index=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)


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
        verbose_name='Количество',
        validators=[MinValueValidator(1)],)

    class Meta:
        verbose_name = 'Соответствие ингредиента и рецепта'
        verbose_name_plural = 'Таблица соответствия ингредиентов и рецептов'
        constraints = (
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            ),
        )


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favoriting',
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favoriting',
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('user', 'recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_recipe'
            ),
        )


class SaleList(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='sale_cart',
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sale_cart',
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('user', 'recipe')
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_sale_cart'
            ),
        )
