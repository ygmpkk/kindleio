from django.conf.urls import patterns, url

urlpatterns = patterns('kindleio.hackernews.views',
    url(r'^$', 'fetch', name='hackernews_fetch'),
    url(r'^check/$', 'check_for_sending', name='hackernews_check_for_sending'),
)

