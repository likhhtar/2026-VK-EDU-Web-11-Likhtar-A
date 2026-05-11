from django.conf import settings
from django.db import models
from django.templatetags.static import static


class DefaultModel(models.Model):
    class Meta:
        abstract = True

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено в')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано в')
    is_active = models.BooleanField(default=True, verbose_name='Активно?')


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

    def __str__(self):
        return f"Профиль пользователя #{self.user_id}"

    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        return static('img/avatar.svg')
