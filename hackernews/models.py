import logging
import os
from urllib2 import URLError

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.encoding import smart_str
from django.utils.timezone import now

from kindleio.models import logger
from kindleio.utils.briticle import Briticle


EMAIL_COUNT_LIMIT = 14
POINTS_LIMITS = (100, 149, 200, 249, 300, 349, 400, 500)
POINTS_LIMIT_TO_SAVE = POINTS_LIMITS[0]
POINTS_LIMIT_PAIRS = ((100, "100 (approximately 20 articles per day)"),
               (149, "149 (approximately 14 articles per day)"),
               (200, "200 (approximately 8 articles per day)"),
               (249, "249 (approximately 5 articles per day)"),
               (300, "300 (approximately 3 articles per day)"),
               (349, "349 (approximately 2 articles per day)"),
               (400, "400 (rare)"),
               (500, "500 (very rare)")
)


class RecoredManager(models.Manager):
    def create_receive_list(self, news, points, file_):
        if self.filter(news=news).exists():
            return
        from kindleio.hackernews.utils import get_email_list
        email_list = get_email_list(points)
        flag = len(email_list) == 0
        record = self.create(news=news, file_path=file_, sent=flag)
        for email in email_list:
            if not SendLog.objects.filter(record=record, email=email).exists():
                SendLog.objects.create(record=record, email=email)

    def update_receive_list(self, news, points, former_points=None):
        if not self.filter(news=news).exists():
            return
        record = self.get(news=news)
        from kindleio.hackernews.utils import get_email_list
        email_list = get_email_list(points, former_points)
        for email in email_list:
            if not SendLog.objects.filter(record=record, email=email).exists():
                SendLog.objects.create(record=record, email=email)
        if len(email_list) > 0:
            record.sent = False
            record.save()


class UserConfig(models.Model):
    user = models.OneToOneField(User)
    disabled = models.BooleanField(default=False)
    points = models.IntegerField(default=300)


class HackerNewsManager(models.Manager):
    def update_news(self, article_list):
        """
        Update HackerNews records:
        1. Add news when it doesnot exist
        2. Update points when changed
        3. Update datetime when saving to file
        """
        count_logged = count_filed = 0
        former_points = None
        for article in article_list:
            logger.info("Enter article:" + article['title'])
            if self.filter(url=article['url']).exists():
                news = self.get(url=article['url'])
                former_points = news.points
                news.points = article['points']
                news.save()
                logger.info("[if] news update.")
            else:
                news = self.create(url=article['url'],
                    points=article['points'],
                    title=smart_str(article['title']))
                count_logged += 1
                logger.info("[else] news created.")

            # Save articles to file whose points big enough
            if article['points'] >= POINTS_LIMIT_TO_SAVE and not news.filed:
                logger.info("article points is high enough, and not filed, try to ...")
                try:
                    br = Briticle(news.url, sent_by="Kindle.io")
                except Exception, e:
                    if isinstance(e, URLError) or 'timed out' in str(e):
                        logger.info("URLError or Time out Exception: %s URL: %s" % (e, news.url))
                        continue
                    raise
                logger.info("... Briticle object fetch ok. len: %s" % len(br.content))

                try:
                    mobi = br.save_to_file(settings.HACKER_NEWS_DIR, title=news.title)
                    logger.info("... filed it ok!")
                except Exception, e:
                    logger.info("Failed to save fiel: %s URL: %s" % (e, news.url))
                    continue
                if mobi:
                    news.filed = True
                    news.added = now()
                    news.save()
                    Record.objects.create_receive_list(news, news.points, mobi)
                    logger.info("Record created.")
                    count_filed += 1
                else:
                    logger.error("Failed to save file. URL: %s" % news.url)

            if news.filed:
                Record.objects.update_receive_list(news, news.points, former_points)
                logger.info("Record updated.")
            else:
                logger.info("This is end, not filed, low points?.")

        return count_logged, count_filed

class HackerNews(models.Model):
    url = models.CharField(max_length=512)
    title = models.CharField(max_length=512, blank=True, null=True)
    points = models.IntegerField(default=0)
    added = models.DateTimeField(auto_now_add=True)
    filed = models.BooleanField(default=False)

    objects = HackerNewsManager()

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return self.title
    __unicode__ = __str__
    __repr__ = __str__

class Record(models.Model):
    news = models.OneToOneField(HackerNews)
    file_path = models.CharField(max_length=512)
    sent = models.BooleanField(default=False)
    added = models.DateTimeField(auto_now_add=True)

    objects = RecoredManager()

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return str(self.news)
    __unicode__ = __str__
    __repr__ = __str__

class SendLog(models.Model):
    record = models.ForeignKey(Record)
    email = models.CharField(max_length=80)
    sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]


def create_user_config(sender, instance, created, **kwargs):
    if created:
        UserConfig.objects.create(user=instance)

post_save.connect(create_user_config, sender=User)
