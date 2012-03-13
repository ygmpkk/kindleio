import urllib2
from bs4 import BeautifulSoup
from django.conf import settings
from kindleio.utils.mail import GSMTP


def get_soup_by_url(url, timeout=10):
    page = urllib2.urlopen(url, timeout=timeout)
    try:
        soup = BeautifulSoup(page, from_encoding='utf8')
    except UnicodeEncodeError:
        soup = BeautifulSoup(page, from_encoding='gb18030')
    return soup


def send_files_to(files, send_to):
    info = "Docs from Kindle.io"
    stmp = GSMTP(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    stmp.send_mail(send_to, info, info, files=files)


def send_to_kindle(request, files):
    email = request.user.email
    if not email:
        return
    send_to = [email]
    info = "Docs from Kindle.io"
    stmp = GSMTP(settings.KINDLEIO_EMAIL, settings.KINDLEIO_EMAIL_PASSWD)
    stmp.send_mail(send_to, info, info, files=files)

