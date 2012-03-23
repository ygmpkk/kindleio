from datetime import timedelta

from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.utils.timezone import now

from kindleio.accounts.models import UserProfile, UUID
from kindleio.notes.utils import get_twitter_private_api


def get_user_from_uuid(uuid):
    date_limit = now() - timedelta(days=1)
    uuids = UUID.objects.filter(uuid=uuid, added__gte=date_limit)
    if not uuids or len(uuids) != 1:
        return None
    return uuids[0].user


def create_or_update_user(user_id, attr):
    """
    Currently, attr must be one of ("douban", "twitter")
    """
    if not user_id or not attr:
        return

    if attr not in ("douban", "twitter"):
        return
    
    username = attr + "_" + user_id
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
    else:
        user = User.objects.create_user(username=username)

    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    attr_name = attr + '_id'
    if getattr(profile, attr_name) != user_id:
        setattr(profile, attr_name, user_id)
        profile.save()
        if attr == 'twitter' and not settings.DEBUG:
            api = get_twitter_private_api()
            api.CreateFriendship(user_id)
    user_logged_in.send(sender=user.__class__, user=user)
    return user

