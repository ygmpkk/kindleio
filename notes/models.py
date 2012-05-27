from django.contrib.auth.models import User
from django.db import models


class Note(models.Model):
    user = models.ForeignKey(User)
    url = models.CharField(max_length=128, blank=True)
    text = models.CharField(max_length=1024)
    remark = models.CharField(max_length=128, blank=True)
    book = models.CharField(max_length=128, blank=True)
    author = models.CharField(max_length=128, blank=True)
    added = models.DateTimeField()
    uuid = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["-added"]

    def __unicode__(self):
        return self.text

    def get_absolute_url(self):
        if self.pk:
            return "http://kindle.io/notes/%s/" % self.uuid
        return ""

    def author(self):
        if self.user.first_name:
            return self.user.first_name
        else:
            return self.user.username

    def title(self):
        return self.text[:20]

class Word(models.Model):
    user = models.ForeignKey(User)
    url = models.CharField(max_length=128, blank=True)
    word = models.CharField(max_length=64)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added"]

    def __unicode__(self):
        return self.word
