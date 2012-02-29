from django.contrib import admin
from kindleio.hackernews.models import HackerNews, UserConfig, Record, SendLog


class HackerNewsAdmin(admin.ModelAdmin):
    search_fields = ['title', 'url']
    list_display = ("title", "points", "added", 'filed')
    list_filter = ('added', 'filed')

class UserConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "disabled")

class RecordAdmin(admin.ModelAdmin):
    list_display = ("news", "added", "sent")

class SendLogAdmin(admin.ModelAdmin):
    list_display = ("record", "email", "sent")
    

admin.site.register(HackerNews, HackerNewsAdmin)
admin.site.register(UserConfig, UserConfigAdmin)
admin.site.register(Record, RecordAdmin)
admin.site.register(SendLog, SendLogAdmin)
