from django.contrib import admin
from kindleio.hackernews.models import HackerNews, UserConfig


class HackerNewsAdmin(admin.ModelAdmin):
    search_fields = ['title', 'url']
    list_display = ("title", "points", "added", 'filed')
    list_filter = ('added', 'filed')

class UserConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "disabled")

admin.site.register(HackerNews, HackerNewsAdmin)
admin.site.register(UserConfig, UserConfigAdmin)
