import os.path
import time
from django.conf import settings
from django.utils.encoding import smart_str
from kindleio.utils.zongheng import get_chapter_content, VIP

def write_to_file(book_id, chapter_list, book_name):
    if not chapter_list:
        return

    if len(chapter_list) == 1:
        file_name = "%s(%s).txt" % (book_name, chapter_list[0].split(' ')[0])
    else:
        left = chapter_list[0][1].split(' ')[0]
        right = chapter_list[-1][1].split(' ')[0]
        file_name = "%s(%s-%s).txt" % (book_name, left, right)
    file_name = os.path.join(settings.ZONGHENG_DIR, file_name)
    with open(file_name, "w") as f:
        for cid, titile in chapter_list:
            content = get_chapter_content(book_id, cid)
            if content == VIP:
                return VIP
            content = "\r\n" + get_chapter_content(book_id, cid)
            f.write(smart_str(content))
            time.sleep(0.3) # sleep a while to be gentle
    return file_name

