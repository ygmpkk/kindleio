from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from kindleio.hackernews.utils import get_user_points, is_hn_disabled

DOUBAN_LOGIN_FLAG = "loged_with_douban"
TWITTER_LOGIN_FLAG = "loged_with_twitter"


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    # Other fields here
    douban_id = models.CharField(max_length=20, null=True, blank=True)
    twitter_id = models.CharField(max_length=40, null=True, blank=True)

    kindle_email = models.CharField(max_length=80, null=True, blank=True)

    def hn_points(self):
        return get_user_points(self.user)

    def hn_disabled(self):
        return is_hn_disabled(self.user)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)
