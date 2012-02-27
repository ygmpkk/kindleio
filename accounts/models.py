from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

DOUBAN_LOGIN_ATTR = "loged_with_douban"


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    # Other fields here
    douban_id = models.CharField(max_length=20, null=True, blank=True)
    twitter_id = models.CharField(max_length=40, null=True, blank=True)

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)
