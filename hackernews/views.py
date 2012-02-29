import os
from urllib2 import URLError

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt

from kindleio.models import logger
from kindleio.hackernews.models import HackerNews
from kindleio.hackernews.utils import HackerNewsArticle
from kindleio.utils.mail import send_mail
from kindleio.utils.decorators import admin_required


@csrf_exempt
@admin_required
def fetch(request):
    if request.method == "POST":
        hn = HackerNewsArticle(fetch=True)
        count_logged, count_filed = HackerNews.objects.update_news(hn.articles)
        return HttpResponse("Find %s news (filed %s).\n" % (count_logged, count_filed))
    raise Http404


@csrf_exempt
@admin_required
def send(request):
    send_to = settings.KINDLE_SENDING_LIST
    subject = "Docs of HackerNews from mitnk.com"
    files = os.listdir(settings.HACKER_NEWS_DIR)
    files = [os.path.join(settings.HACKER_NEWS_DIR, x) for x in files if (x.endswith('.mobi') or x.endswith(".txt"))]
    if not files:
        return HttpResponse("No new articles filed")

    try:
        info = "%s files sent.\n" % len(files)
        send_mail(send_to, subject, info, files=files)
    except Exception, e:
        info = "send_mail() failed."
        logger.error(info)
    else:
        for f in files:
            os.remove(f)
    return HttpResponse(info)


def orld(request):
    if not url.startswith('http'):
        url = 'http://' + url

    try:
        br = Briticle(url)
    except Exception, e:
        if isinstance(e, URLError) or 'timed out' in str(e):
            logger.info("URLError or Time out Exception: %s URL: %s" % (e, url))
            return HttpResponse("Internal Time Out.")
        raise

    doc_file = br.save_to_file(settings.KINDLE_LIVE_DIR)
    if doc_file:
        if not settings.DEBUG:
            send_mail([settings.MY_KINDLE_MAIL,], "New documentation here", "Sent from mitnk.com", files=[doc_file,])
            os.remove(doc_file)
        return HttpResponse("%s Sent!" % doc_file)
    else:
        return HttpResponse("Error: No file generated. URL: %s" % url)
