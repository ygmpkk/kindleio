from cgi import parse_qs

import pydouban
from oauthtwitter import OAuthApi
import twitter, oauth

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from kindleio.accounts.decorators import login_required
from kindleio.accounts.utils import create_user_via_douban_id, create_user_via_twitter_id
from kindleio.accounts.models import UserProfile
from kindleio.hackernews.models import POINTS_LIMIT_PAIRS
from kindleio.hackernews.utils import get_limit_points, set_user_points, set_hn_disabled



def register(request):
    # Cannot allow user rgister usernames begin with "douban_" or "twitter_"
    pass


@login_required
def profile(request):
    user = request.user
    error_info = ""
    update_succeed = None
    if request.method == "POST":
        if request.POST.has_key("first_name"):
            first_name = request.POST.get("first_name")
            if first_name:
                user.first_name = first_name
                user.save()
                update_succeed = True
            kindle_email = request.POST.get("kindle_email")
            if kindle_email:
                if ("@" in kindle_email) and kindle_email.endswith("kindle.com"):
                    profile = request.user.get_profile()
                    profile.kindle_email = kindle_email
                    profile.save()
                    update_succeed = True
                else:
                    error_info = "Invalid email, must ends with @kindle.com"
                    update_succeed = False

        else:
            receive_hn = request.POST.get("receive_hn", None)
            set_hn_disabled(user, (not receive_hn))
            if receive_hn:
                points = request.POST.get("points_limit", 500)
                points = get_limit_points(points)
                if points:
                    set_user_points(user, points)
            update_succeed = True
    return render_to_response("profile.html",
                              {'error_info': error_info,
                               'update_succeed': update_succeed,
                               "points_list": POINTS_LIMIT_PAIRS,
                              },
                              context_instance=RequestContext(request))


def site_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.session.get("next_url", "")
            return HttpResponseRedirect(next_url or "/")
        else:
            request.session["login_error_info"] = "Invalid username or password, please try again."
            site_login = reverse("site_login")
            next_url = request.session.get("next_url", "")
            if next_url:
                site_login += "?next=%s" % next_url
            return HttpResponseRedirect(site_login)
    else:
        next_url = request.GET.get("next", "")
        if next_url:
            request.session["next_url"] = next_url
        login_error_info = request.session.get("login_error_info")
        if login_error_info:
            del request.session['login_error_info']
    return render_to_response('login.html',
                              {"login_error_info": login_error_info},
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
