import time

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt

from kindleio.accounts.decorators import login_required
from kindleio.hackernews.models import HackerNews, SendRecord, EMAIL_COUNT_LIMIT
from kindleio.hackernews.utils import HackerNewsArticle, send_file_to_kindles
from kindleio.hackernews.utils import get_limit_points, set_user_points, set_hn_disabled
from kindleio.models import logger
from kindleio.utils.decorators import admin_required


@login_required
def config(request):
    if request.method == "POST":
        user = request.user
        receive_hn = request.POST.get("receive_hn", None)
        set_hn_disabled(user, (not receive_hn))
        if receive_hn:
            points = request.POST.get("points_limit", 500)
            points = get_limit_points(points)
            if points:
                set_user_points(user, points)
        request.session['config_updated'] = True
    url = reverse("accounts_profile")
    return HttpResponseRedirect(url)

@csrf_exempt
@admin_required
def fetch(request):
    if request.method == "POST":
        hn = HackerNewsArticle(fetch=True)
        count_created, count_updated, count_filed = HackerNews.objects.update_news(hn.articles)
        return HttpResponse("News saved %s, updated %s, and filed %s.\n" % (count_created, count_updated, count_filed))
    raise Http404


@csrf_exempt
@admin_required
def check_for_sending(request):
    news_list = HackerNews.objects.filter(sent=False)
    count_file = 0
    count_email = 0
    for news in news_list:
        no_receivers_left = False
        sr_list = SendRecord.objects.filter(news=news, sent=False)
        if len(sr_list) > EMAIL_COUNT_LIMIT:
            sr_list = sr_list[:EMAIL_COUNT_LIMIT]
        else:
            no_receivers_left = True

        receivers = [x.email for x in sr_list]
        try:
            send_file_to_kindles(news.file_path, receivers)
            count_file += 1
            count_email += len(receivers)
        except Exception, e:
            info = "send_mail() failed. Exception: %s File: %s" % (e, news.file_path)
            logger.error(info)
        else:
            sr_list.update(sent=True)
            if no_receivers_left:
                news.sent = True
                news.save()
            time.sleep(0.3) # sleep for a while before sending next mail (if any).
    return HttpResponse("%s file sent to %s emails.\n" % (count_file, count_email))
