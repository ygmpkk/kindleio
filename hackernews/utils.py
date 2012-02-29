import os
import shelve

from kindleio.hackernews.models import UserConfig, SendLog, POINTS_LIMITS
from kindleio.models import logger
from kindleio.utils import get_soup_by_url
from kindleio.utils.mail import send_mail


def get_limit_points(points):
    try:
        points = int(points)
    except ValueError:
        pass
    else:
        for p in POINTS_LIMITS:
            if points <= p:
                return p
    return POINTS_LIMITS[-1]

def get_email_list(points, points_from=None):
    if points_from:
        ucs = UserConfig.objects.filter(points__lte=points, points__gt=points_from)
    else:
        ucs = UserConfig.objects.filter(points__lte=points)
    email_list = []
    for uc in ucs:
        kindle_email = uc.user.get_profile().kindle_email
        if kindle_email:
            email_list.append(kindle_email)
    return email_list

def get_user_points(user):
    if UserConfig.objects.filter(user=user).exists():
        return UserConfig.objects.get(user=user).points
    return 0

def set_user_points(user, points):
    if UserConfig.objects.filter(user=user).exists():
        uc = UserConfig.objects.get(user=user)
        uc.points = points
        uc.save()
        return True
    return False

def send_file_to_kindles(doc, receive_list):
    subject = "Docs of HackerNews from Kindle.io"
    send_mail(receive_list, subject, subject, files=[doc])

def is_hn_disabled(user):
    if UserConfig.objects.filter(user=user).exists():
        return UserConfig.objects.get(user=user).disabled
    return False

def set_hn_disabled(user, disabled):
    if UserConfig.objects.filter(user=user).exists():
        uc = UserConfig.objects.get(user=user)
        uc.disabled = disabled
        uc.save()
        return True
    return False

class HackerNewsArticle(object):
    POINTS_MIN_LIMIT = 70

    def __str__(self):
        return u"<HackerNewsArticle %s articles insider>" % len(self.articles)

    __unicode__ = __str__
    __repr__ = __str__

    def __init__(self, fetch=False):
        self.url = 'http://news.ycombinator.com/'
        self.articles = []
        if fetch:
            self.fetch()

    def fetch(self):
        def is_home_page(url):
            return '/' not in url.replace('//', '').strip('/')

        try:
            soup = get_soup_by_url(self.url)
        except:
            logger.info("Time out when fetching HackerNewsArticle.")
            return

        # Reset articles before fetching
        self.articles = []

        tags = soup.find("table").find_all("td", {"class": "title"})
        for tag in tags:
            tag_a = tag.find('a')
            if (not tag_a) or \
                ('href' not in tag_a.attrs) or \
                (len(tag_a.contents) > 1) or \
                (tag_a.string.lower() == "more" and '/' not in tag_a['href']):
                continue

            try:
                points = int(tag.parent.nextSibling.find('span').string.split(' ')[0])
            except AttributeError, ValueError:
                points = 0

            if 'http' not in tag_a['href']:
                tag_a['href'] = "http://news.ycombinator.com/" + tag_a['href']

            if tag_a['href'] and points >= self.POINTS_MIN_LIMIT and (not is_home_page(tag_a['href'])):
                self.articles.append({
                    'url': tag_a['href'],
                    'title': tag_a.string,
                    'points': points,
                })
