import datetime
import re
import rfc822
import urllib2

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from kindleio.accounts.decorators import login_required
from kindleio.accounts.models import UserProfile
from kindleio.models import logger
from kindleio.utils import get_soup_by_url
from kindleio.utils.decorators import admin_required
from kindleio.notes.models import Note, Word
from kindleio.notes.utils import get_twitter_private_api

ASCII_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


@login_required
def index(request):
    book = request.GET.get("book")
    if book:
        notes = Note.objects.filter(user=request.user, book=book)
        if not notes:
            return HttpResponseRedirect(reverse("notes_index"))

    else:
        notes = Note.objects.filter(user=request.user)
    return render_to_response("notes.html",
        {'notes': notes},
        context_instance=RequestContext(request))


@login_required
def config(request):
    if request.method == "POST":
        twitter_id = request.POST.get("twitter_id", "").strip()
        if twitter_id.startswith('@'):
            twitter_id = twitter_id[1:]
        if not twitter_id:
            messages.error(request, "Twitter ID needed.")
        elif '@' in twitter_id:
            messages.error(request, "Invalid Twitter ID. It should like @kindleio")
        else:
            profile = request.user.get_profile()
            if profile.twitter_id != twitter_id:
                if UserProfile.objects.filter(twitter_id=twitter_id).exists():
                    messages.error(request, "This twitter id was already set by others.")
                else:
                    try:
                        if not settings.DEBUG:
                            api = get_twitter_private_api()
                            api.CreateFriendship(twitter_id)
                    except Exception, e:
                        messages.error(request, "Failed when following your account, please try again.")
                    else:
                        profile.twitter_id = twitter_id
                        profile.save()
                        messages.success(request, "Your twitter id was set successfully.")
    return HttpResponseRedirect(reverse("accounts_profile"))


@csrf_exempt
@admin_required
def check(request):
    api = get_twitter_private_api()
    try:
        messages = api.GetHomeTimeline()
    except (urllib2.URLError, urllib2.HTTPError), e:
        logger.error("HTTPError: %s" % e)
        return HttpResponse("Error.")

    info = []
    for msg in messages:
        if "#Kindle" not in msg.text or 'http' not in msg.text:
            continue
        url = re.search(r'(http[^ ]+)', msg.text).group(1)
        if Note.objects.filter(url=url).exists() or Word.objects.filter(url=url).exists():
            continue
        user = get_user_from_twitter_id(msg.user.screen_name)
        if not user:
            continue
        added = datetime.datetime(*rfc822.parsedate(msg.created_at)[:6])
        info.append((user, url, added))

    count = 0
    for user, url, added in info:
        save_note(user, url, added)
        count +=  1
    return HttpResponse("%s\n" % count)

def get_user_from_twitter_id(user_name):
    users = User.objects.filter(userprofile__twitter_id=user_name)
    if users:
        return users[0]
    return None

def save_note(user, url, date=None):
    soup = get_soup_by_url(url)
    tag = soup.find("div", {'class': 'highlightText'})
    text = ''.join(tag.findAll(text=True)).strip()

    remark = ''
    tag = soup.find("div", {'class': 'note'})
    if tag:
        remark = ''.join(tag.findAll(text=True)).replace('Note:', '').replace('@zzrt', '').strip()

    cover_tag = soup.find('div', {'class': 'cover'})
    tag = cover_tag.find("span", {'class': 'title'})
    if tag:
        book = ''.join(tag.findAll(text=True)).strip()
        if 'Personal Document' in book:
            book = ''
    else:
        book = ''

    tag = cover_tag.find("span", {'class': 'author'})
    if tag:
        author = ''.join(tag.findAll(text=True)).replace(' by ', '').strip()
    else:
        author = ''

    if ' ' not in text \
        and text[0] in ASCII_CHARS \
        and len(text) <= 64:
        if Word.objects.filter(word=text).count() == 0:
            Word.objects.create(user=user, url=url, word=text)
    else:
        note = Note(user=user, url=url, text=text)
        note.added = date or datetime.datetime.now()
        if remark:
            note.remark = remark
        if book:
            note.book = book
        if author:
            note.author = author
        note.save()

