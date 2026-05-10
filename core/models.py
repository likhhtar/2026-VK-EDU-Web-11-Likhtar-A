from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='пользователь',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='аватар',
    )
    rating = models.PositiveIntegerField(default=0, verbose_name='рейтинг')

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'
        db_table = 'core_profile'

    def __str__(self):
        return f'Profile({self.user.username})'
