import datetime
import re
import rfc822
import string
import urllib2
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from kindleio.accounts.decorators import login_required
from kindleio.accounts.models import UserProfile
from kindleio.accounts.oauthtwitter import OAuthApi
from kindleio.accounts.utils import get_twitter_api
from kindleio.models import logger
from kindleio.utils import get_soup_by_url
from kindleio.utils.decorators import admin_required
from kindleio.notes.models import Note, Word
from kindleio.notes.utils import get_twitter_private_api, shorten_status_urls


@login_required
def index(request):
    book = request.GET.get("book")
    if book:
        notes = Note.objects.filter(user=request.user, book=book)
        if not notes:
            return HttpResponseRedirect(reverse("notes_index"))
    else:
        notes = Note.objects.filter(user=request.user)
    context = {'notes': notes, 'book': book}
    return render(request, "notes/notes.html", context)

def view_note(request, uuid):
    note = get_object_or_404(Note, uuid=uuid)
    return render(request, "notes/view_note.html", {'note': note})

@login_required
def link_twitter_account(request):
    api = OAuthApi(settings.TWITTER_CONSUMER_KEY,
                   settings.TWITTER_CONSUMER_SECRET)
    request_token = api.getRequestToken()
    request.session["twitter_request_token"] = request_token.to_string()
    request.session["link_twitter_account"] = True
    authorization_url = api.getAuthorizationURL(request_token)
    return HttpResponseRedirect(authorization_url)

@login_required
def unlink_twitter_account(request):
    profile = request.user.get_profile()
    profile.twitter_token = ""
    profile.save()
    return HttpResponseRedirect(reverse("accounts_profile"))

@csrf_exempt
@admin_required
def check(request):
    api = get_twitter_private_api()
    try:
        messages = api.GetHomeTimeline(count=100)
    except:
        logger.error("Error when GetHomeTimeline when checking Notes")
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
        info.append((user, url, added, msg.id))
    count = 0
    for user, url, added, tweet_id in info:
        save_note(user, url, added, tweet_id)
        count +=  1
    return HttpResponse("%s\n" % count)

def get_user_from_twitter_id(user_name):
    users = User.objects.filter(userprofile__twitter_id=user_name)
    if users:
        return users[0]
    return None

def save_note(user, url, date, tweet_id):
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
        and text[0] in string.ascii_letters \
        and len(text) <= 64:
        if Word.objects.filter(word=text).count() == 0:
            Word.objects.create(user=user, url=url, word=text)
    else:
        note = Note(user=user, url=url, text=text)
        note.uuid = str(uuid.uuid4())
        note.added = date or datetime.datetime.now()
        if remark:
            note.remark = remark[:128]
        if book:
            note.book = book[:128]
        if author:
            note.author = author[:128]
        note.save()

        # Delete this tweet and tweet it's content
        user_api = get_twitter_api(user=user)
        if not user_api:
        	return

        if len(text) <= 140:
            status = text
            if len(status) + len(" #note") <= 140:
                status += " #note"
            if remark and len(status) + len(remark) <= 138:
                status = remark + ": " + status
            try:
                user_api.PostUpdates(status)
                user_api.DestroyStatus(tweet_id)
            except Exception, e:
                logger.info("Error: %s tweeted: %s, delete: %s", e, status, tweet_id)
        else:
            # len(u".. #note http://t.co/al28lfq5xx") == 32; 140 - 32 = 108
            status = text[:108] + ".. #note http://kindle.io" + note.get_absolute_url()
            status = shorten_status_urls(status)
            if len(status) > 140:
                status = text[:130] + "... #note"
            try:
                user_api.PostUpdates(status)
                user_api.DestroyStatus(tweet_id)
            except Exception, e:
                logger.info("Error: %s tweeted: %s, delete: %s", e, status, tweet_id)
