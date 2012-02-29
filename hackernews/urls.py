from django.conf.urls import patterns, url

urlpatterns = patterns('kindleio.hackernews.views',
    url(r'^$', 'fetch', name='hackernews_fetch'),
)

