import re
import urllib
import urllib2

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

def get_short_url(url):
    try:
        short_url = "http://is.gd/api.php?longurl=" + urllib.quote(url)
        content = urllib2.urlopen(short_url).read()
        return content
    except:
        pass
    return ""

def shorten_urls_proc(res):
    url = res.group('url')
    if len(url) > 30:
        short_url = get_short_url(url)
        return short_url if short_url else url
    return url

def shorten_status_urls(text):
    try:
        p = re.compile(r'(?P<url>https?://[^ ]+)', re.VERBOSE)
        return p.sub(shorten_urls_proc, text)
    except:
        return text
