import re
import urllib2
from bs4 import BeautifulSoup


USER_AGENT = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16"
ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
COOKIE = 'WAPPageSize=0'
HEADERS = [('User-agent', USER_AGENT), ("Accept", ACCEPT), ("Cookie", COOKIE)]

VIP = "VIP"


def get_top_books(click=1, new=None):
    """
    >>> len(get_rank()) == 15
    True
    >>> len(get_rank(new=1)) == 50
    True
    """
    try:
        if new:
            url = 'http://m.zongheng.com/rank/new'
        else:
            url = 'http://m.zongheng.com/rank?rankType=1&timeType=3'
        opener = urllib2.build_opener()
        opener.addheaders = HEADERS
        page = opener.open(url)
    except (urllib2.HTTPError, urllib2.URLError):
        return []
    soup = BeautifulSoup(page, from_encoding="utf-8")
    tag = soup.find("div", {"class": "list"})
    a_tags = tag.findAll("a", recursive=False)
    return [(int(x['href'].replace(r"/book?bookid=", "")), x.string) for x in a_tags]


def get_chapter_list(book_id, asc=0, page=1):
    """
    >>> L = get_chapter_list(48552, asc=1, page=3); print len(L), L[0][0], L[-1][0]
    20 1215151 1232898
    """
    if not book_id:
        return []

    try:
        url = 'http://m.zongheng.com/chapter/list?bookid=%s&asc=%s&pageNum=%s'
        opener = urllib2.build_opener()
        opener.addheaders = HEADERS
        page = opener.open(url % (book_id, asc, page))
    except (urllib2.HTTPError, urllib2.URLError):
        return []

    soup = BeautifulSoup(page, from_encoding="utf-8")
    tag = soup.find("div", {"class": "list"})
    if not tag:
        return []

    chapter_id_list = []
    a_tags = tag.findAll('a')
    for a in a_tags:
        href = a['href']
        results = re.search(r'cid=(\d+)', href)
        if results:
            title = a.string.strip()
            chapter_id_list.append((int(results.group(1)), title))
    return chapter_id_list

def get_book_name(book_id):
    """
    >>> get_book_name(45669)
    u'\u4fee\u771f\u4e16\u754c'
    """
    url = 'http://m.zongheng.com/book?bookid=%s' % book_id
    opener = urllib2.build_opener()
    opener.addheaders = HEADERS
    name = ""
    try:
        page = opener.open(url)
        soup = BeautifulSoup(page, from_encoding="utf-8")
    except (urllib2.HTTPError, urllib2.URLError):
        pass
    else:
        name = soup.find("h2").find("a").string.strip().strip(u'\u300a\u300b').replace(' ', '')
    return name


def get_book_pages(book_id, asc=1, page=1):
    """
    >>> get_book_pages(45669, 1, 10)
    [1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 28]
    """
    def is_a_tag_with_page_number(tag):
        return tag.name == "a" and tag.string and re.compile(r"^\d+$").search(tag.string)

    def is_start_page(tag):
        return tag.name == "a" and tag.string and tag.string == "<<"

    def is_end_page(tag):
        return tag.name == "a" and tag.string and tag.string == ">>"

    try:
        url = 'http://m.zongheng.com/chapter/list?bookid=%s&asc=%s&pageNum=%s' % (book_id, asc, page)
        opener = urllib2.build_opener()
        opener.addheaders = HEADERS
        page = opener.open(url)
    except (urllib2.HTTPError, urllib2.URLError):
        return []

    soup = BeautifulSoup(page, from_encoding="utf-8")
    start = soup.find(is_start_page)
    pattern = r'pageNum=(\d+)'
    if start and re.compile(pattern).search(start['href']):
        result = re.search(pattern, start['href'])
        start = int(result.group(1))
    end = soup.find(is_end_page)
    if end and re.compile(pattern).search(end['href']):
        result = re.search(pattern, end['href'])
        end = int(result.group(1))

    a_tags = soup.findAll(is_a_tag_with_page_number)
    return [start] + [int(x.string) for x in a_tags] + [end]


def get_chapter_content(book_id, chapter_id):
    """
    >>> abs(len(get_chapter_content(45669, 1843837)) - 3395) < 10
    True
    >>> get_chapter_content(127431, 2824029) == VIP
    True
    """
    url = 'http://m.zongheng.com/chapter?bookid=%s&cid=%s' % (book_id, chapter_id)
    opener = urllib2.build_opener()
    opener.addheaders = HEADERS
    page = opener.open(url)
    soup = BeautifulSoup(page, from_encoding="utf-8")
    tag = soup.find("div", {"class": "yd"})
    if not tag:
        return VIP
    metas = tag.findAll(["a", "span"])
    for meta in metas:
        meta.extract()
    p_tags = tag.findAll("p")
    # Kindle needs two '\n\n' to display a line break.
    line_break = u"\n\n"
    for p in p_tags:
        if p.string and isinstance(p.string, unicode):
            p.string = p.string + line_break
        else:
            p.string = line_break
    return tag.get_text()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
