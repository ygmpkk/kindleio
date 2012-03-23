from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


DOUBAN_LOGIN_FLAG = "loged_with_douban"
TWITTER_LOGIN_FLAG = "loged_with_twitter"


class UUID(models.Model):
    user = models.ForeignKey(User)
    uuid = models.CharField(max_length=40)
    added = models.DateTimeField(auto_now_add=True)


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    # Other fields here
    douban_id = models.CharField(max_length=20, null=True, blank=True)
    twitter_id = models.CharField(max_length=40, null=True, blank=True)

    def hn_points(self):
        from kindleio.hackernews.utils import get_user_points
        return get_user_points(self.user)

    def email(self):
        return self.user.email

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
