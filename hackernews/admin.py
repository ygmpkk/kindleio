from django.contrib import admin
from kindleio.hackernews.models import HackerNews, UserConfig, SendRecord, \
    Weekly, WeeklySendRecord


class HackerNewsAdmin(admin.ModelAdmin):
    search_fields = ['title', 'url']
    list_display = ("title", "points", "added", 'filed')
    list_filter = ('added', 'filed')

class UserConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "receive_weekly")

class SendRecordAdmin(admin.ModelAdmin):
    list_display = ("news", "email", "sent", "added")

class WeeklySendRecordAdmin(admin.ModelAdmin):
    list_display = ("weekly", "email", "sent", "added")

admin.site.register(HackerNews, HackerNewsAdmin)
admin.site.register(UserConfig, UserConfigAdmin)
admin.site.register(SendRecord, SendRecordAdmin)
admin.site.register(Weekly)
admin.site.register(WeeklySendRecord, WeeklySendRecordAdmin)
