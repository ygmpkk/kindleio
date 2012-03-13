from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from kindleio.hackernews.utils import get_user_points

DOUBAN_LOGIN_FLAG = "loged_with_douban"
TWITTER_LOGIN_FLAG = "loged_with_twitter"


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    # Other fields here
    douban_id = models.CharField(max_length=20, null=True, blank=True)
    twitter_id = models.CharField(max_length=40, null=True, blank=True)

    def hn_points(self):
        return get_user_points(self.user)

    def email(self):
        return self.user.email

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
