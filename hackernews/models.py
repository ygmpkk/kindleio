import datetime
import logging
import os
import re
import subprocess
from datetime import timedelta
from urllib2 import URLError

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import smart_str
from django.utils.timezone import now

from kindleio.models import logger
from kindleio.utils.briticle import BriticleFile
from kindleio.hackernews import signals


DISABLED = 7777777
EMAIL_COUNT_LIMIT = 14
POINTS_LIMITS = (200, 249, 300, 349, 400, 500, DISABLED)
POINTS_LIMIT_TO_SAVE = POINTS_LIMITS[0]
POINTS_LIMIT_PAIRS = (
    (DISABLED, "Do Not Send to Me"),
    (200, "200 (approximately 8 articles per day)"),
    (249, "249 (approximately 5 articles per day)"),
    (300, "300 (approximately 3 articles per day)"),
    (349, "349 (approximately 2 articles per day)"),
    (400, "400 (rare)"),
    (500, "500 (very rare)")
)


class HackerNewsManager(models.Manager):
    def generate_weekly(self):
        date_now = now()
        year = date_now.isocalendar()[0]
        week_number = date_now.isocalendar()[1] - 1
        dir_weekly = os.path.join(settings.HACKER_NEWS_DIR, str(year), "%02d" % week_number)
        file_weekly = os.path.join(dir_weekly, 'HackerNews_Weekly_%02d.html' % week_number)
        mobi_file = re.sub(r'\.html$', '.mobi', file_weekly)
        if Weekly.objects.filter(week_number=week_number).exists():
            return "Error: this Weekly already generated"
        if os.path.exists(mobi_file):
            return mobi_file

        ten_days_age = date_now - datetime.timedelta(days=10)
        results = self.filter(added__gt=ten_days_age,
                              points__gt=POINTS_LIMIT_TO_SAVE,
                              filed=True)

        idx = 1
        toc = u'<a name="toc"></a><ul>\r\n'
        html = u""
        for news in results:
            if news.added.isocalendar()[1] != week_number:
                continue
            html_file = re.sub(r'\.\w+$', '.html', news.file_path)
            if not os.path.exists(html_file):
                continue
            with open(html_file) as file_to_read:
                html += u'<mbp:pagebreak/><a name="%02d"></a>' % idx
                content = file_to_read.read()
                html += content.decode('utf8')
                html += u'<br><br><a href="#toc">Go to table of content</a>'
                toc += u'<li><a href="#%02d">%s</a></li>\r\n' % (idx, news.title)
                idx += 1

        if idx == 1:
            # No available articles for this weekly
            return None

        toc += u"</ul><mbp:pagebreak/>\r\n"

        with open(file_weekly, 'w') as f:
            f.write(u'<html><head><meta http-equiv="content-type" content="text/html; charset=utf-8">')
            f.write(u'<title>HackerNews Weekly %s</title></head><body>' % week_number)
            f.write(u'<h1>HackerNews Weekly %s</h1>' % week_number)
            f.write(toc.encode('utf8'))
            f.write(html.encode('utf8'))
            f.write(u'</body></html>')

        nut_mobi_name = re.sub(r'.html$', '.mobi', (file_weekly.split('/')[-1]))
        cmd = ["kindlegen", file_weekly, "-o", nut_mobi_name]
        subprocess.call(cmd)
        os.remove(file_weekly)
        if not os.path.exists(mobi_file):
            return None
        Weekly.objects.create(week_number=week_number, file_path=mobi_file)
        return mobi_file

    def update_news(self, article_list):
        """
        Update HackerNews records
        """
        count_created = count_updated = count_filed = 0
        for article in article_list:
            if self.filter(url=article['url']).exists():
                news = self.get(url=article['url'])

                # Update the points of the article, send the points update signal
                if news.filed and news.file_path and article['points'] > news.points:
                    pre_points = news.points
                    news.points = article['points']
                    news.save()
                    signals.points_updated.send(sender=news, pre_points=pre_points)
                    count_updated += 1

                # If the article is abort before. Ignore it.
                # We can check the error log for reasons
                if news.aborted:
                    continue

            else:
                # Create an new one if it does not exist
                news = self.create(url=article['url'],
                                   points=article['points'],
                                   title=smart_str(article['title']))
                count_created += 1

            # Save article whose points is high enough into file
            if (not news.filed) and article['points'] >= POINTS_LIMIT_TO_SAVE:
                try:
                    year, week_number, _ = datetime.date.today().isocalendar()
                    dir_hackernews = settings.HACKER_NEWS_DIR 
                    if not os.path.exists(dir_hackernews):
                        os.mkdir(dir_hackernews)
                    dir_year = os.path.join(dir_hackernews, str(year))
                    if not os.path.exists(dir_year):
                        os.mkdir(dir_year)
                    dir_week = os.path.join(dir_year, "%02d" % week_number)
                    if not os.path.exists(dir_week):
                        os.mkdir(dir_week)
                    bf = BriticleFile(news.url, dir_week)
                except Exception, e:
                    if isinstance(e, URLError) or 'timed out' in str(e):
                        logger.error("URLError or Time out Exception: %s URL: %s" % (e, news.url))
                        news.aborted = True
                        news.save()
                        continue
                    elif isinstance (e, UnicodeEncodeError):
                        logger.error("UnicodeEncodeError: %s URL: %s" % (e, news.url))
                        news.aborted = True
                        news.save()
                        continue
                    raise

                # Abort if there is not content
                if bf.is_empty():
                    logger.info("No content found for: %s" % news.url)
                    news.aborted = True
                    news.save()
                    continue

                try:
                    mobi = bf.save_to_mobi(title=news.title, sent_by="Kindle.io")
                except Exception, e:
                    logger.error("Failed while calling bf.save_to_mobi(). %s: %s URL: %s" % \
                                 (e.__class__, e, news.url))
                    news.aborted = True
                    news.save()
                    continue

                if mobi:
                    news.filed = True
                    news.file_path = mobi
                    news.html = bf.html
                    news.save()
                    signals.file_saved.send(sender=news)
                    count_filed += 1
                else:
                    logger.error("Failed to save file. URL: %s" % news.url)
                    news.aborted = True
                    news.save()

        return count_created, count_updated, count_filed

class HackerNews(models.Model):
    url = models.CharField(max_length=512)
    title = models.CharField(max_length=512, blank=True, null=True)
    points = models.IntegerField(default=0)
    filed = models.BooleanField(default=False)
    file_path = models.CharField(max_length=512)
    sent = models.BooleanField(default=True)
    added = models.DateTimeField(auto_now_add=True)
    html = models.TextField(blank=True, null=True)
    aborted = models.BooleanField(default=False)

    objects = HackerNewsManager()

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return "<HackerNews: %s>" % self.title
    __unicode__ = __str__
    __repr__ = __str__


class SendRecord(models.Model):
    news = models.ForeignKey(HackerNews)
    email = models.CharField(max_length=80)
    sent = models.BooleanField(default=False)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added"]


class UserConfig(models.Model):
    user = models.OneToOneField(User)
    points = models.IntegerField(default=300)
    receive_weekly = models.BooleanField(default=True)

    def __unicode__(self):
        return u"HackerNews Config " + self.user.username


class Weekly(models.Model):
    week_number = models.IntegerField()
    file_path = models.CharField(max_length=512)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added"]

    def __unicode__(self):
        return u"<HackerNews Weekly %02d>" % self.week_number


class WeeklySendRecord(models.Model):
    weekly = models.ForeignKey(Weekly)
    email = models.CharField(max_length=80)
    sent = models.BooleanField(default=False)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added"]


@receiver(signals.points_updated)
def update_receive_list(sender, pre_points, **kwargs):
    from kindleio.hackernews.utils import get_email_list
    email_list = get_email_list(sender.points, pre_points)
    for email in email_list:
        if not SendRecord.objects.filter(news=sender, email=email).exists():
            SendRecord.objects.create(news=sender, email=email)
    if len(email_list) > 0:
        sender.sent = False
        sender.save()

@receiver(signals.file_saved)
def create_receive_list(sender, **kwargs):
    from kindleio.hackernews.utils import get_email_list
    email_list = get_email_list(sender.points)
    for email in email_list:
        if not SendRecord.objects.filter(news=sender, email=email).exists():
            SendRecord.objects.create(news=sender, email=email)
    if len(email_list) > 0:
        sender.sent = False
        sender.save()

@receiver(post_save, sender=User, dispatch_uid="create_hackernews_config")
def create_user_config(sender, instance, created, **kwargs):
    if created:
        UserConfig.objects.create(user=instance)


@receiver(post_save, sender=Weekly, dispatch_uid="create_weekly")
def create_weekly(sender, instance, created, **kwargs):
    if created:
        from kindleio.hackernews.utils import get_weekly_receivers
        for email in get_weekly_receivers():
            WeeklySendRecord.objects.create(weekly=instance, email=email)

