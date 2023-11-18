from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2'
                ),
            },
        ),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'subscriber')
    list_filter = ('author', 'subscriber')
    list_per_page = 5
    search_fields = ('author',)


admin.site.site_title = 'Администрирование Foodgram'
admin.site.site_header = 'Администрирование Foodgram'
