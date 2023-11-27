from django.contrib.auth.models import AbstractUser
from django.db import models

from api.constants import USERNAME_FIELD, REQUIRED_FIELDS


class User(AbstractUser):
    email = models.EmailField(max_length=USERNAME_FIELD, blank=False,
                              verbose_name='email',
                              unique=True)
    first_name = models.CharField(max_length=REQUIRED_FIELDS, blank=False,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=REQUIRED_FIELDS, blank=False,
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
