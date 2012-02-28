from django.contrib import auth
from django.utils.functional import SimpleLazyObject
from kindleio.accounts.models import UserProfile, DOUBAN_LOGIN_FLAG, TWITTER_LOGIN_FLAG


def get_user(request):
    douban_id = request.session.get("douban_user_id")
    twitter_id = request.session.get("twitter_id")
    if douban_id:
        try:
            user = UserProfile.objects.get(douban_id=douban_id).user
        except UserProfile.DoesNotExist:
            request.session.flush()
        else:
            setattr(user, DOUBAN_LOGIN_FLAG, True)
            request._cached_user = user
    elif twitter_id:
        try:
            user = UserProfile.objects.get(twitter_id=twitter_id).user
        except UserProfile.DoesNotExist:
            request.session.flush()
        else:
            setattr(user, TWITTER_LOGIN_FLAG, True)
            request._cached_user = user
    if not hasattr(request, '_cached_user'):
        request._cached_user = auth.get_user(request)
    return request._cached_user


class AuthenticationMiddleware(object):
    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: get_user(request))

