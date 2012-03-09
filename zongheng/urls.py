from django.conf.urls.defaults import *

urlpatterns = patterns('kindleio.zongheng.views',
    url(r'^$', 'index', name="zongheng_index"),
)
