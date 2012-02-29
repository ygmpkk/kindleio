from django.conf import settings
from django.http import HttpResponseForbidden, Http404

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.method == "POST" and request.POST.get("key") != settings.API_SECRET_KEY:
            raise Http404
        return view_func(request, *args, **kwargs)
    return wrapper
