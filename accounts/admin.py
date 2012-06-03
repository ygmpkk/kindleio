from django.contrib import admin
from kindleio.accounts.models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['user', 'douban_id', 'twitter_id']
    list_display = ['user', 'douban_id', 'twitter_id', 'email', 'has_twitter_token']

admin.site.register(UserProfile, UserProfileAdmin)
