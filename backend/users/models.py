from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.constants import EMAIL_FIELD_CONST, USER_NAME_FIELD_CONST


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']
    email = models.EmailField(max_length=EMAIL_FIELD_CONST, blank=False,
                              verbose_name='email',
                              unique=True)
    first_name = models.CharField(max_length=USER_NAME_FIELD_CONST,
                                  blank=False,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=USER_NAME_FIELD_CONST, blank=False,
                                 verbose_name='Фамилия'
                                 )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='subscriber',
                                   verbose_name='Подписчик')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='author',
                               verbose_name='Автор')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=['author', 'subscriber'],
                name='unique_subscription'),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('author')),
                name='self_subscribe',
            ))
