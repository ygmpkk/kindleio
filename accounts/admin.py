from django.contrib import admin
from kindleio.accounts.models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['user', 'douban_id', 'twitter_id']
    list_display = ['user', 'douban_id', 'twitter_id', 'email', 'hn_points']

admin.site.register(UserProfile, UserProfileAdmin)
