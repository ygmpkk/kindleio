from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from kindleio.hackernews.models import HackerNews, Record, SendLog, EMAIL_COUNT_LIMIT
from kindleio.hackernews.utils import HackerNewsArticle, send_file_to_kindles
from kindleio.models import logger
from kindleio.utils.decorators import admin_required

@csrf_exempt
@admin_required
def fetch(request):
    if request.method == "POST":
        hn = HackerNewsArticle(fetch=True)
        count_logged, count_filed = HackerNews.objects.update_news(hn.articles)
        return HttpResponse("Saved %s news (filed %s).\n" % (count_logged, count_filed))
    raise Http404


@csrf_exempt
@admin_required
def check_for_sending(request):
    record_list = Record.objects.filter(sent=False)
    count_file = 0
    count_email = 0
    for record in record_list:
        less_than_limit = False
        sl = SendLog.objects.filter(record=record, sent=False)
        if len(sl) > EMAIL_COUNT_LIMIT:
            sl = sl[:EMAIL_COUNT_LIMIT]
        else:
            less_than_limit = True

        receivers = [x.email for x in sl]
        try:
            send_file_to_kindles(record.file_path, receivers)
            count_file += 1
            count_email += len(receivers)
        except Exception, e:
            info = "send_mail() failed. %s" % e
            logger.error(info)
        else:
            sl.update(sent=True)
            if less_than_limit:
                record.sent = True
                record.save()
    return HttpResponse("%s file sent to %s emails.\n" % (count_file, count_email))
