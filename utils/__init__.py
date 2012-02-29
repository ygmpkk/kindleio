import urllib2
from bs4 import BeautifulSoup


def get_soup_by_url(url, timeout=10):
    page = urllib2.urlopen(url, timeout=timeout)
    try:
        soup = BeautifulSoup(page, from_encoding='utf8')
    except UnicodeEncodeError:
        soup = BeautifulSoup(page, from_encoding='gb18030')
    return soup
