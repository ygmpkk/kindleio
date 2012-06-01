from cgi import parse_qs
import os
import uuid

from kindleio.accounts import pydouban, oauth
from kindleio.accounts.oauthtwitter import OAuthApi

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from kindleio.accounts.decorators import login_required
from kindleio.accounts.models import UUID
from kindleio.accounts.utils import create_or_update_user, \
    get_user_from_uuid, set_user_twitter_token, get_twitter_api
from kindleio.hackernews.models import POINTS_LIMIT_PAIRS
from kindleio.utils import generate_file, send_files_to


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        if not username:
            messages.error(request, "Username cannot be blank")
        elif not password:
            messages.error(request, "Password cannot be blank")
        elif not email:
            messages.error(request, "Kindle E-mail cannot be blank")
        elif not email.endswith('@kindle.com') and \
            not email.endswith('@free.kindle.com'):
            messages.error(request,
                           "Kindle E-mail must ends with @kindle.com "
                           "or @free.kindle.com")
        elif username.startswith("twitter_") or \
            username.startswith("douban_") or \
            User.objects.filter(username=username).exists():
            messages.error(request, "This username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "This Kindle E-mail already exists.")
        else:
            user = User.objects.create_user(username,
                                            password=password, email=email)
            messages.success(request, "Account has been created successfully!")
            user = authenticate(username=username, password=password)
            login(request, user)
            return HttpResponseRedirect(reverse("accounts_profile"))
    return HttpResponseRedirect(reverse("site_login"))


@login_required
def profile(request):
    if request.method == "POST":
        user = request.user
        first_name = request.POST.get("first_name")
        if first_name and user.first_name != first_name:
            messages.success(request, "Your profile was updated successfully")
            user.first_name = first_name
            user.save()

        email = request.POST.get("email", "").strip()
        if (not email.endswith("@free.kindle.com")) and \
            not email.endswith("@kindle.com"):
            messages.error(request,
                           "Invalid email, must end with @kindle.com "
                           "or @free.kindle.com")
        elif not email.split("@")[0]:
            messages.error(request, "Invalid email")
        else:
            prefix = email.split('@')[0] + '@'
            users = User.objects.filter(email__startswith=prefix)
            if len(users) >= 1 and users[0] != user:
                messages.error(request,
                               "This kindle email has already used by others.")
            else:
                # User can change email from @kindle.com to @free.kindle.com
                user.email = email
                user.save()
                messages.success(request,
                                 "Your Kindle E-mail was updated successfully")
        return HttpResponseRedirect(reverse("accounts_profile"))
    else:
        return render_to_response("profile.html",
                                  { "points_list": POINTS_LIMIT_PAIRS, },
                                  context_instance=RequestContext(request))


def site_login(request):
    # Redirect to Home if already logged in.
    if not isinstance(request.user, AnonymousUser):
        return HttpResponseRedirect("/")

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        if username.split('@')[0] and \
            (username.endswith('@kindle.com') or \
            username.endswith('@free.kindle.com')):
            prefix = username.split('@')[0]
            result = User.objects.filter(email__startswith=prefix + '@',
                email__endswith='kindle.com')
            if result and len(result) == 1:
                username = result[0].username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
            return HttpResponseRedirect(reverse("site_login"))

        auth_user = authenticate(username=user.username, password=password)
        if auth_user is not None:
            login(request, auth_user)
            next_url = request.session.get("next_url", "")
            if next_url:
                del request.session['next_url']
            return HttpResponseRedirect(next_url or "/")
        else:
            info = "Invalid username or password"
            if username.startswith("twitter_"):
                info = "It seems you signed up with Twitter, " \
                       "Please Login with Twitter."
            elif username.startswith("douban_"):
                info = "It seems you signed up with Douban, " \
                       "Please Login with Douban."
            messages.error(request, info)
            return HttpResponseRedirect(reverse("site_login"))
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
    auth = pydouban.Auth(key=settings.DOUBAN_API_KEY,
                         secret=settings.DOUBAN_SECRET)
    callback_url = "http://%s%s" % \
                   (request.META["HTTP_HOST"], reverse("douban_callback"))
    dic = auth.login(callback=callback_url)
    key, secret = dic['oauth_token'], dic['oauth_token_secret']
    request.session["douban_request_secret"] = secret
    return HttpResponseRedirect(dic['url'])


def douban_callback(request):
    request_key = request.GET.get("oauth_token")
    request_secret = request.session.get("douban_request_secret")
    auth = pydouban.Auth(key=settings.DOUBAN_API_KEY,
                         secret=settings.DOUBAN_SECRET)

    access_tokens = auth.get_acs_token(request_key, request_secret)
    tokens = parse_qs(access_tokens)
    request.session["douban_oauth_token"] = tokens["oauth_token"][0]
    request.session["douban_oauth_token_secret"] = tokens["oauth_token_secret"][0]
    request.session["douban_user_id"] = tokens["douban_user_id"][0]

    # Create a user if not exist
    douban_id = request.session['douban_user_id']
    create_or_update_user(douban_id, "douban")

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
    token = request.session["douban_oauth_token"]
    token_secret = request.session["douban_oauth_token_secret"]
    api.set_oauth(key=settings.DOUBAN_API_KEY,
                  secret=settings.DOUBAN_SECRET,
                  acs_token=token,
                  acs_token_secret=token_secret)
    return api

def login_with_twitter(request):
    api = OAuthApi(settings.TWITTER_CONSUMER_KEY,
                   settings.TWITTER_CONSUMER_SECRET)
    request_token = api.getRequestToken()
    request.session["twitter_request_token"] = request_token.to_string()
    authorization_url = api.getAuthorizationURL(request_token)
    return HttpResponseRedirect(authorization_url)


def twitter_callback(request):
    token_string = request.session.get('twitter_request_token')
    if not token_string:
        messages.error(request, "Invalid Twitter Token.")
        return HttpResponseRedirect(reverse("site_login"))
    req_token = oauth.Token.from_string(token_string)
    api = OAuthApi(settings.TWITTER_CONSUMER_KEY,
                   settings.TWITTER_CONSUMER_SECRET,
                   req_token.key,
                   req_token.secret)
    access_token = api.getAccessToken()
    request.session["access_token"] = access_token.to_string()
    if 'twitter_request_token' in request.session:
        del request.session["twitter_request_token"]
    api = get_twitter_api(request)
    try:
        twitter_user = api.GetUserInfo()
    except:
        messages.error(request, "Network Error, Please Try Again.")
        return HttpResponseRedirect(reverse("accounts_profile"))

    screen_name = twitter_user.screen_name
    request.session["twitter_id"] = screen_name # what does this for?

    if request.session.get("link_twitter_account", False):
        del request.session["link_twitter_account"]
        set_user_twitter_token(request.user, screen_name, access_token.to_string())
        return HttpResponseRedirect(reverse("accounts_profile"))
    else:
        user = create_or_update_user(screen_name, "twitter")
        set_user_twitter_token(user, screen_name, access_token.to_string())
        next_url = request.session.get("next_url", reverse("accounts_profile"))
        return HttpResponseRedirect(next_url)

def password_reset(request):
    url = reverse('site_login')

    uuid_string = request.GET.get('uuid')
    if uuid_string:
        ## Branch 1: Render password reset page
        if not get_user_from_uuid(uuid_string):
            return HttpResponse("Invalid URL")
        return render_to_response("accounts/password_reset.html",
                                  { "uuid": uuid_string, },
                                  context_instance=RequestContext(request))

    uuid_string = request.POST.get('uuid')
    if uuid_string:
        ## Branch 2: Reset Password if received an valid uuid
        user = get_user_from_uuid(uuid_string)
        if not user:
            return HttpResponse("Invalid URL")

        url = reverse("accounts_password_reset") + "?uuid=" + uuid_string
        new_password = request.POST.get('password')
        new_password2 = request.POST.get('password2')
        if not new_password:
            messages.error(request, "Password cannot be blank.")
            return HttpResponseRedirect(url)
        elif new_password2 != new_password:
            messages.error(request, "The passwords typed do not match.")
            return HttpResponseRedirect(url)
        else:
            user.set_password(new_password)
            user.save()
            UUID.objects.get(uuid=uuid_string).delete()
            messages.success(request,
                             "The password has been reset successfully.")
            url = reverse('site_login')
            return HttpResponseRedirect(url)

    ## Branch else: Send reset URL to user's Kindle
    if request.method == "POST":
        email = request.POST.get('email')
        if not email or (not email.endswith('@kindle.com') and \
                         not email.endswith('@free.kindle.com')):
            messages.error(request, "Email address required.")
            return HttpResponseRedirect(url)
        elif not User.objects.filter(email__startswith=email.split("@")[0] + '@'):
            messages.error(request, "No user with this E-mail Address.")
            return HttpResponseRedirect(url)

        prefix = email.split('@')[0]
        result = User.objects.filter(email__startswith=prefix + '@',
            email__endswith='kindle.com')
        if result and len(result) == 1:
            user = result[0]
            uuid_string = str(uuid.uuid4())
            UUID.objects.create(user=user, uuid=uuid_string)
            reset_url = "http://kindle.io" + reverse("accounts_password_reset") + \
                        "?uuid=" + uuid_string
            text = "Hello,\n\nPlease click the following URL to reset your password. " \
                   "The URL will be invalid in 24 hours." \
                   "\n\n%s\n\nKindle.io" % reset_url
            f = generate_file(text)
            if not settings.DEBUG:
                send_files_to([f], [email])
                os.remove(f)
            messages.success(request,
                             "Password Reset URL has been sent to your Kindle."
                             " Please check it in a few minutes.")
    return HttpResponseRedirect(url)
