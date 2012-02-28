from django.contrib.auth.models import User
from kindleio.accounts.models import UserProfile


def create_user_via_douban_id(douban_id):
    if not douban_id:
        return

    username = "douban_" + douban_id
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
    else:
        user = User.objects.create(username=username)

    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    if not profile.douban_id:
        profile.douban_id = douban_id
        profile.save()


def create_user_via_twitter_id(twitter_id):
    if not twitter_id:
        return

    username = "twitter_" + twitter_id
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
    else:
        user = User.objects.create(username=username)

    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    if not profile.twitter_id:
        profile.twitter_id = twitter_id
        profile.save()
