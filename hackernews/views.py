import datetime
import time

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

from kindleio.accounts.decorators import login_required
from kindleio.hackernews.models import (HackerNews, SendRecord,
    UserConfig, EMAIL_COUNT_LIMIT)
from kindleio.hackernews.utils import HackerNewsArticle
from kindleio.hackernews.utils import get_limit_points
from kindleio.models import logger
from kindleio.utils import send_files_to
from kindleio.utils.decorators import admin_required


@csrf_exempt
@admin_required
def generate_weekly(request):
    mobi = HackerNews.objects.generate_weekly()
    logger.info("Generating Weekly: %s" % mobi)
    return HttpResponse("Weekly mobi generated: %s\n" % mobi)


@csrf_exempt
@admin_required
def weekly_sending(request):
    date_now = now()
    week_number = date_now.isocalendar()[1] - 1
    weekly = Weekly.objects.get(week_number=week_number)
    receivers = WeeklySendRecord.objects.filter(weekly=weekly, send=False)[:EMAIL_COUNT_LIMIT]
    emails = [x.email for x in receivers]
    if len(emails) == 0:
        info = "Weekly %02d sent complete."
        logger.info(info)
        return HttpResponse(info + "\n")

    try:
        send_files_to([news.file_path], emails)
    except Exception, e:
        info = "send weekly mail failed. Exception: %s" % e
        logger.error(info)
    else:
        for item in receivers:
            item.sent = True
            item.save()
    return HttpResponse("Weekly sent one round successfully!\n")


@login_required
def config(request):
    if request.method == "POST":
        uc = UserConfig.objects.get(user=request.user)
        points = request.POST.get("points_limit", 500)
        points = get_limit_points(points)
        if points:
            uc.points = points
        receive_weekly = request.POST.get("receive_weekly", None)
        uc.receive_weekly = (receive_weekly is not None)
        uc.save()
        messages.success(request, "Your HackerNews profile was updated successfully")
    return HttpResponseRedirect(reverse("accounts_profile"))

@csrf_exempt
@admin_required
def fetch(request):
    if request.method == "POST":
        hn = HackerNewsArticle(fetch=True)
        created, updated, filed = HackerNews.objects.update_news(hn.articles)
        return HttpResponse("News saved %s, updated %s, and filed %s.\n" %
                            (created, updated, filed))
    raise Http404


@csrf_exempt
@admin_required
def check_for_sending(request):
    """ TODO: UT needed."""
    one_week_ago = now()  - datetime.timedelta(days=7)
    news_list = HackerNews.objects.filter(added__gt=one_week_ago, sent=False)
    count_file = 0
    count_email = 0
    for news in news_list:
        sr_list = SendRecord.objects.filter(news=news, sent=False)[:EMAIL_COUNT_LIMIT]
        if len(sr_list) == 0:
            news.sent = True
            news.save()
            continue

        receivers = [x.email for x in sr_list]
        try:
            send_files_to([news.file_path], receivers)
            count_file += 1
            count_email += len(receivers)
        except Exception, e:
            info = ("send mail failed. Exception: %s File: %s" %
                    (e, news.file_path))
            logger.error(info)
        else:
            for sr in sr_list:
                sr.sent = True
                sr.save()
            time.sleep(0.3)
    return HttpResponse("%s file sent to %s emails.\n" %
                        (count_file, count_email))
