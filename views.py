import os
from urllib2 import URLError

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext

from kindleio.accounts.decorators import login_required, is_authenticated
from kindleio.models import logger
from kindleio.utils.decorators import kindle_email_required
from kindleio.utils.briticle import BriticleFile
from kindleio.utils import send_to_kindle

def index(request):
    if is_authenticated(request.user):
    	return home(request)
    else:
        return about(request)

@login_required
@kindle_email_required
def home(request):
    if request.method == "POST":
        url = request.POST.get("url")
        if not url.startswith('http'):
            url = 'http://' + url

        if '.' not in url:
            messages.error(request, "Need a valid URL.")
            return HttpResponseRedirect("/")

        try:
            bf = BriticleFile(url, settings.KINDLE_LIVE_DIR)
        except Exception, e:
            if isinstance(e, URLError) or 'timed out' in str(e):
                logger.info("URLError or Time out Exception: %s URL: %s" % (e, url))
            elif isinstance (e, UnicodeEncodeError):
                logger.info("UnicodeEncodeError: %s URL: %s" % (e, url))
            raise

        doc = bf.save_to_mobi(sent_by="Kindle.io")
        if doc:
            if not settings.DEBUG:
                send_to_kindle(request, [doc], subject=bf.title)
                os.remove(doc)
            messages.success(request, "The doc has been sent to your kindle successfully!")
            return HttpResponseRedirect("/")
        else:
            messages.error(request, "Error: No file generated for this URL.")
            return HttpResponseRedirect("/")
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')
