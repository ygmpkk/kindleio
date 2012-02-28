import datetime
import logging
import os
from urllib2 import URLError

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.encoding import smart_str

from kindleio.utils.briticle import Briticle

logger = logging.getLogger("HackerNews")
if not logger.handlers:
    handler = logging.FileHandler(settings.LOG_BRITICLE)
    formatter = logging.Formatter('%(asctime)s %(levelname)s\n%(message)s\n')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

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
        for article in article_list:
            try:
                news = self.get(url=article['url'])
                news.points = article['points']
                news.save()
            except self.model.DoesNotExist:
                news = self.model(url=article['url'],
                    points=article['points'],
                    title=smart_str(article['title'])
                )
                news.save()
                count_logged += 1

            # Save articles to file whose points big enough
            if article['points'] >= settings.POINTS_LIMIT_TO_KINDLE and (not news.filed):
                try:
                    br = Briticle(news.url)
                except Exception, e:
                    if isinstance(e, URLError) or 'timed out' in str(e):
                        logger.info("URLError or Time out Exception: %s URL: %s" % (e, news.url))
                        continue
                    raise

                mobi = br.save_to_file(settings.HACKER_NEWS_DIR, title=news.title)
                if mobi:
                    news.filed = True
                    news.added = datetime.datetime.now()
                    news.save()
                    count_filed += 1
                else:
                    logger.error("Failed to save file. URL: %s" % news.url)
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


def create_user_config(sender, instance, created, **kwargs):
    if created:
        UserConfig.objects.create(user=instance)

post_save.connect(create_user_config, sender=User)
