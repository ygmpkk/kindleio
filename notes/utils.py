from django.conf import settings
from kindleio.accounts.oauthtwitter import OAuthApi
from kindleio.accounts import oauth


def get_twitter_private_api():
    token = settings.KINDLEIO_TWITTER_TOKEN
    return get_twitter_api(token)

def get_twitter_api(token):
    access_token = oauth.Token.from_string(token)
    api = OAuthApi(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET, 
                   access_token.key, access_token.secret, verified=True)
    return api

