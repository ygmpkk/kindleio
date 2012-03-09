from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from kindleio.accounts.decorators import login_required
from kindleio.utils.decorators import kindle_email_required
from kindleio.zongheng.utils import write_to_file
from kindleio.utils import send_to_kindle
from kindleio.utils.zongheng import (get_chapter_list, get_top_books, VIP,
    get_book_name, get_book_pages)


@csrf_exempt
@login_required
@kindle_email_required
def index(request):
    pages = []
    chapter_list = []
    top_books = []
    new_books = []

    book_id = request.POST.get('book_id')
    from_ = int(request.POST.get('from', 0))
    to_ = int(request.POST.get('to', 0))
    cpage = request.POST.get('cpage', 1)

    # Final step. Chapter from and to is set, send them to kindle
    if from_ and to_ and book_id and cpage:
        if from_ > to_:
            from_, to_ = to_, from_
        book_name = get_book_name(book_id)
        chapter_list = get_chapter_list(book_id, asc=0, page=cpage)
        chapter_list = [x for x in chapter_list if from_ <= x[0] <= to_]
        chapter_list.reverse()
        file_name = write_to_file(book_id, chapter_list, book_name=book_name)
        if file_name == VIP:
            messages.error(request, "No content found, VIP chapters found.")
        else:
            send_to_kindle(request, [file_name])
            messages.success(request, "These chapters have beed sent to your Kindle.")
        return HttpResponseRedirect(reverse("zongheng_index"))

    # Step before the final, client is walking through pages of the book
    elif book_id and cpage:
        pages = get_book_pages(book_id, page=cpage)
        chapter_list = get_chapter_list(book_id, asc=0, page=cpage)

    # the client just submit a book_id, show the latest chapters and its pages
    elif book_id:
        pages = get_book_pages(book_id)
        chapter_list = get_chapter_list(book_id, asc=0, page=1)

    # first come to this page, show the top books
    else:
        top_books = get_top_books()
        new_books = get_top_books(new=1)
    return render_to_response('zongheng/index.html',
                              {'pages': pages,
                               'cpage': int(cpage),
                               'book_id': book_id,
                               'top_books': top_books,
                               'new_books': new_books,
                               'chapter_list': chapter_list, },
                              context_instance=RequestContext(request))
