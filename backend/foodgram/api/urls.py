from django.urls import include, path
from rest_framework import routers

from .views import IngredientViewSet, RecipeViewSet, TagViewSet
from .views import CustomUserViewSet

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken'))
]
