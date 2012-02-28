from django.contrib import admin
from kindleio.accounts.models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['user', 'douban_id', 'twitter_id', 'kindle_email']
    list_display = ['user', 'douban_id', 'twitter_id', 'kindle_email', 'hn_points', 'hn_disabled']

admin.site.register(UserProfile, UserProfileAdmin)

