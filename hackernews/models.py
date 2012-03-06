import logging
import os
from urllib2 import URLError

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import smart_str
from django.utils.timezone import now

from kindleio.models import logger
from kindleio.utils.briticle import Briticle
from kindleio.hackernews import signals


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


class HackerNewsManager(models.Manager):
    def update_news(self, article_list):
        """
        Update HackerNews records:
        1. Add news when it doesnot exist
        2. Update points when it exists
        3. Update datetime when saving to file (just for quering convenience)
        """
        count_created = count_updated = count_filed = 0
        for article in article_list:
            logger.info("Enter article:" + article['title'])
            if self.filter(url=article['url']).exists():
                news = self.get(url=article['url'])
                if news.filed and news.file_path and article['points'] > news.points:
                    pre_points = news.points
                    news.points = article['points']
                    news.save()
                    signals.points_updated.send(sender=news, pre_points=pre_points)
                    count_updated += 1
            else:
                news = self.create(url=article['url'],
                    points=article['points'],
                    title=smart_str(article['title']))
                count_created += 1
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
                    news.file_path = mobi
                    news.added = now()
                    news.save()
                    signals.file_saved.send(sender=news)
                    count_filed += 1
                else:
                    logger.error("Failed to save file. URL: %s" % news.url)
        return count_created, count_updated, count_filed

class HackerNews(models.Model):
    url = models.CharField(max_length=512)
    title = models.CharField(max_length=512, blank=True, null=True)
    points = models.IntegerField(default=0)
    filed = models.BooleanField(default=False)
    file_path = models.CharField(max_length=512)
    sent = models.BooleanField(default=True)
    added = models.DateTimeField(auto_now_add=True)

    objects = HackerNewsManager()

    class Meta:
        ordering = ["-added"]

    def __str__(self):
        return self.title
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
    disabled = models.BooleanField(default=False)
    points = models.IntegerField(default=300)

    def __unicode__(self):
        return u"HackerNews Config " + self.user.username


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
