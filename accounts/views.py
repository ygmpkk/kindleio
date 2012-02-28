from cgi import parse_qs

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from kindleio.accounts.models import UserProfile

import pydouban
from oauthtwitter import OAuthApi
import twitter, oauth


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


def profile(request):
    return HttpResponse("The profile page.")

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
    try:
        up = UserProfile.objects.get(douban_id=douban_id)
    except UserProfile.DoesNotExist:
        api = get_douban_api(request)
        people = api.get_people(douban_id)
        username = people['title']['t']
        if User.objects.filter(username=username).exists():
            new_name = "douban_" + douban_id
            if not User.objects.filter(username=new_name).exists():
                user = User.objects.create(username=new_name)
                up = user.get_profile()
                up.douban_id = douban_id
                up.save()
        else:
            user = User.objects.create(username=username)
            up = user.get_profile()
            up.douban_id = douban_id
            up.save()
        
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
    user = api.GetUserInfo()
    request.session["twitter_id"] = user.screen_name

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
