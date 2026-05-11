from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Profile

admin.site.site_header = 'Администрирование EDU-Web'
admin.site.index_title = 'Панель управления'
admin.site.site_title = 'EDU-Web'


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    max_num = 1


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'rating', 'has_avatar')
    list_filter = ('rating',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)

    @admin.display(description='аватар', boolean=True)
    def has_avatar(self, obj: Profile) -> bool:
        return bool(obj.avatar and obj.avatar.name)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


if admin.site.is_registered(User):
    admin.site.unregister(User)
admin.site.register(User, UserAdmin)
