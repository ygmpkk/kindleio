import os
from urllib2 import URLError

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from kindleio.accounts.decorators import login_required
from kindleio.utils.briticle import Briticle
from kindleio.utils.mail import send_mail

@login_required
def home(request):
    kindle_email = request.user.get_profile().kindle_email
    if not kindle_email:
        messages.error(request, "Please set up you Send To Kindle Email.")
        return HttpResponseRedirect(reverse("accounts_profile"))

    if request.method == "POST":
        url = request.POST.get("url")
        if not url.startswith('http'):
            url = 'http://' + url

        if '.' not in url:
            messages.error(request, "Need a valid URL.")
            return HttpResponseRedirect("/")

        try:
            br = Briticle(url, sent_by="Kindle.io")
        except Exception, e:
            if isinstance(e, URLError) or 'timed out' in str(e).lower():
                messages.error(request, "Internal Time Out. Please try again later.")
                return HttpResponseRedirect("/")
            messages.error(request, "Unknown Error occurred. Did you input a valid URL?")
            return HttpResponseRedirect("/")
        doc = br.save_to_file(settings.KINDLE_LIVE_DIR)
        if doc:
            if not settings.DEBUG:
                send_mail([kindle_email], "New documentation here", "Sent from kindle.io", files=[doc,])
                os.remove(doc)
            messages.success(request, "The doc has been sent to your kindle successfully!")
            return HttpResponseRedirect("/")
        else:
            messages.error(request, "Error: No file generated for this URL.")
            return HttpResponseRedirect("/")
    
    return render_to_response('home.html',
                              context_instance=RequestContext(request))

def about(request):
    return render_to_response('about.html',
                              context_instance=RequestContext(request))
    
