from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, SaleList,
                     Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'count_favorite',)
    inlines = [RecipeIngredientInline, ]
    list_filter = ('author', 'name', 'tags')
    search_fields = ('author', 'name',)

    def count_favorite(self, object):
        """Вычисляет количество добавлений рецепта в избранное."""
        return object.favoriting.count()
    count_favorite.short_description = 'Количество добавлений в избранное'


@admin.register(RecipeIngredient)
class RecipeIngredientstAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ingredient', 'amount', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    list_filter = ('user',)
    search_fields = ('user',)


@admin.register(SaleList)
class SaleListAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    list_filter = ('user',)
    search_fields = ('user',)
