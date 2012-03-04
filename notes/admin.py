from django.contrib import admin
from kindleio.notes.models import Note, Word


class NoteAdmin(admin.ModelAdmin):
    search_fields = ['text', 'remark', 'book', 'author']
    list_display = ("user", "text", "added")

class WordAdmin(admin.ModelAdmin):
    search_fields = ['word']
    list_display = ("user", "word", "added")

admin.site.register(Note, NoteAdmin)
admin.site.register(Word, WordAdmin)
