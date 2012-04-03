from django.conf.urls import patterns, url

urlpatterns = patterns('kindleio.hackernews.views',
    url(r'^$', 'fetch', name='hackernews_fetch'),
    url(r'^check/$', 'check_for_sending', name='hackernews_check_for_sending'),
    url(r'^config/$', 'config', name='hackernews_config'),
    url(r'^generate_weekly/$', 'generate_weekly', name='generate_weekly'),
    url(r'^weekly_sending/$', 'weekly_sending', name='weekly_sending'),
)

