from cgi import parse_qs

import pydouban
from oauthtwitter import OAuthApi
import twitter, oauth

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from kindleio.accounts.decorators import login_required
from kindleio.accounts.utils import create_user_via_douban_id, create_user_via_twitter_id
from kindleio.accounts.models import UserProfile
from kindleio.hackernews.models import POINTS_LIMIT_PAIRS


def signup(request):
    url = reverse("site_login")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if not username or not password:
            messages.error(request, "username and password cannot be blank")
        elif username.startswith("twitter_") or username.startswith("douban_") or \
            User.objects.filter(username=username).exists():
            messages.error(request, "This username already exists.")
        else:
            user = User.objects.create_user(username, password=password)
            messages.success(request, "Account has been created successfully!")
            url = reverse("accounts_profile")
            user = authenticate(username=username, password=password)
            login(request, user)
    return HttpResponseRedirect(url)


@login_required
def profile(request):
    user = request.user
    if request.POST.has_key("first_name") and request.POST.has_key("kindle_email"):
        first_name = request.POST.get("first_name")
        user.first_name = first_name
        user.save()
        kindle_email = request.POST.get("kindle_email", "").strip()
        if not kindle_email:
            messages.error(request, "Please set up you Send to Kindle Email.")
            return HttpResponseRedirect(reverse("accounts_profile"))
        elif (not kindle_email.endswith("@free.kindle.com")) and (not kindle_email.endswith("@kindle.com")):
            messages.error(request, "Invalid email, must end with @kindle.com or @free.kindle.com")
            return HttpResponseRedirect(reverse("accounts_profile"))
        elif UserProfile.objects.filter(kindle_email__startswith=kindle_email.split("@")[0] + '@'):
            messages.error(request, "This kindle email has already used by others.")
            return HttpResponseRedirect(reverse("accounts_profile"))
        else:
            profile = request.user.get_profile()
            profile.kindle_email = kindle_email
            profile.save()
            messages.success(request, "Your profile was updated successfully")
    return render_to_response("profile.html",
                              { "points_list": POINTS_LIMIT_PAIRS, },
                              context_instance=RequestContext(request))


def site_login(request):
    if not isinstance(request.user, AnonymousUser):
        return HttpResponseRedirect("/")

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.session.get("next_url", "")
            return HttpResponseRedirect(next_url or "/")
        else:
            messages.error(request, "Invalid username or password, please try again.")
            site_login = reverse("site_login")
            next_url = request.session.get("next_url", "")
            if next_url:
                site_login += "?next=%s" % next_url
            return HttpResponseRedirect(site_login)
    else:
        next_url = request.GET.get("next", "")
        if next_url:
            request.session["next_url"] = next_url
    return render_to_response('login.html',
                              context_instance=RequestContext(request))


def site_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse("site_login"))


def login_with_douban(request):
    auth = pydouban.Auth(key=settings.DOUBAN_API_KEY, secret=settings.DOUBAN_SECRET)
    callback_url = "http://%s%s" % (request.META["HTTP_HOST"], reverse("douban_callback"))
    dic = auth.login(callback=callback_url)
    key, secret = dic['oauth_token'], dic['oauth_token_secret']
    request.session["douban_request_secret"] = secret
    return HttpResponseRedirect(dic['url'])


def douban_callback(request):
    request_key = request.GET.get("oauth_token")
    request_secret = request.session.get("douban_request_secret")
    auth = pydouban.Auth(key=settings.DOUBAN_API_KEY, secret=settings.DOUBAN_SECRET)

    access_tokens = auth.get_acs_token(request_key, request_secret)
    tokens = parse_qs(access_tokens)
    request.session["douban_oauth_token"] = tokens["oauth_token"][0]
    request.session["douban_oauth_token_secret"] = tokens["oauth_token_secret"][0]
    request.session["douban_user_id"] = tokens["douban_user_id"][0]

    # Create a user if not exist
    douban_id = request.session['douban_user_id']
    create_user_via_douban_id(douban_id)
        
    if "douban_request_secret" in request.session:
        del request.session["douban_request_secret"]
    next_url = request.session.get("next_url", "")
    if not next_url:
        next_url = reverse("accounts_profile")
    return HttpResponseRedirect(next_url)


def get_douban_api(request):
    if "douban_oauth_token" not in request.session or \
        "douban_oauth_token_secret" not in request.session:
        return None

    api = pydouban.Api()
    api.set_oauth(key=settings.DOUBAN_API_KEY, 
                  secret=settings.DOUBAN_SECRET,
                  acs_token=request.session["douban_oauth_token"], 
                  acs_token_secret=request.session["douban_oauth_token_secret"])
    return api


def login_with_twitter(request):
    api = OAuthApi(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
    request_token = api.getRequestToken()
    request.session["twitter_request_token"] = request_token.to_string()
    authorization_url = api.getAuthorizationURL(request_token)
    return HttpResponseRedirect(authorization_url)
    

def twitter_callback(request):
    req_token = oauth.Token.from_string(request.session.get('twitter_request_token'))
    api = OAuthApi(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET, req_token.key, req_token.secret)
    access_token = api.getAccessToken() 
    request.session["access_token"] = access_token.to_string()
    if 'twitter_request_token' in request.session:
        del request.session["twitter_request_token"]

    # save twitter id
    api = get_twitter_api(request)
    user = api.GetUserInfo()
    request.session["twitter_id"] = user.screen_name
    create_user_via_twitter_id(user.screen_name)
    next_url = request.session.get("next_url", "")
    if not next_url:
        next_url = reverse("accounts_profile")
    return HttpResponseRedirect(next_url)


def get_twitter_api(request):
    api = None
    access_token = request.session.get('access_token')
    if access_token: 
        access_token = oauth.Token.from_string(access_token)
        api = OAuthApi(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET, 
                       access_token.key, access_token.secret, verified=True)
    return api
