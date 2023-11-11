from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram.settings import FIELD_NUM_1, FIELD_NUM_2


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=FIELD_NUM_1, blank=False,
                              verbose_name='email',
                              unique=True)
    first_name = models.CharField(max_length=FIELD_NUM_2, blank=False,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=FIELD_NUM_2, blank=False,
                                 verbose_name='Фамилия'
                                 )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                   related_name='subscriber',
                                   verbose_name='Подписчик')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
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
