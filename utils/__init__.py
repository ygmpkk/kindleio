import os
import urllib2
from bs4 import BeautifulSoup
from django.conf import settings
from kindleio.utils.mail import GSMTP


def get_soup_by_url(url, timeout=10):
    try:
        page = urllib2.urlopen(url, timeout=timeout)
    except urllib2.HTTPError:
        return None
    try:
        soup = BeautifulSoup(page, from_encoding='utf8')
    except UnicodeEncodeError:
        soup = BeautifulSoup(page, from_encoding='gb18030')
    return soup


def generate_file(text, title="", file_name=""):
    if not title:
        title = "Message from Kindle.io"
    if not file_name:
        file_name = title.replace(' ', '_')
    if not file_name.endswith('.txt'):
        file_name += '.txt'
    path = os.path.join(settings.KINDLE_LIVE_DIR, file_name)
    with open(path, 'w') as f:
        f.write(text.encode('utf-8'))
    return path


def send_files_to(files, receivers, subject=""):
    info = "Docs from Kindle.io"
    stmp = GSMTP(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    if not subject:
        subject = info
    stmp.send_mail(receivers, subject, info, files=files)


def send_to_kindle(request, files, subject=""):
    email = request.user.email
    if not email:
        return
    send_to = [email]
    info = "Docs from Kindle.io"
    stmp = GSMTP(settings.KINDLEIO_EMAIL, settings.KINDLEIO_EMAIL_PASSWD)
    if not subject:
        subject = info
    stmp.send_mail(send_to, subject, info, files=files)

