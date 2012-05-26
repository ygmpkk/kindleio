from django.conf.urls import patterns, url

urlpatterns = patterns('kindleio.notes.views',
    url(r'^$', 'index', name='notes_index'),
    url(r'^check/$', 'check', name='notes_check'),
    url(r'^config/$', 'config', name='notes_config'),
    url(r'^link_twitter_account/$', 'link_twitter_account', name='notes_link_twitter_account'),
)

