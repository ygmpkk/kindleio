from datetime import timedelta

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.utils.timezone import now

from kindleio.accounts import oauth
from kindleio.accounts.models import UserProfile, UUID
from kindleio.accounts.oauthtwitter import OAuthApi
from kindleio.notes.utils import get_twitter_private_api

def get_twitter_api(request=None, user=None):
    api = None
    access_token = ""

    if request:
        access_token = request.session.get('access_token')
    if not access_token:
        try:
            profile = user.get_profile()
            access_token = profile.twitter_token
        except UserProfile.DoesNotExist:
            pass

    if access_token:
        access_token = oauth.Token.from_string(access_token)
        api = OAuthApi(settings.TWITTER_CONSUMER_KEY,
                       settings.TWITTER_CONSUMER_SECRET,
                       access_token.key, access_token.secret, verified=True)
    return api


def set_user_twitter_token(user, screen_name, token_string):
    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    profile.twitter_id = screen_name
    profile.twitter_token = token_string
    profile.save()
    try:
        api = get_twitter_private_api()
        api.CreateFriendship(screen_name)
    except:
        pass

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
        if attr == 'twitter':
            try:
                api = get_twitter_private_api()
                api.CreateFriendship(user_id)
            except:
                pass
    user_logged_in.send(sender=user.__class__, user=user)
    return user

