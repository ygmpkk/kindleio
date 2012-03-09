from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method != "POST" or request.POST.get("key") != settings.API_SECRET_KEY:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapper


def kindle_email_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.get_profile().kindle_email:
            messages.error(request, "Please set up you Send To Kindle Email.")
            return HttpResponseRedirect(reverse("accounts_profile"))
        return view_func(request, *args, **kwargs)
    return wrapper
