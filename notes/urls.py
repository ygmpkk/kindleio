from django.conf.urls import patterns, url

urlpatterns = patterns('kindleio.notes.views',
    url(r'^$', 'index', name='notes_index'),
    url(r'^check/$', 'check', name='notes_check'),
    url(r'^link_twitter_account/$', 'link_twitter_account', name='notes_link_twitter_account'),
    url(r'^unlink_twitter_account/$', 'unlink_twitter_account', name='notes_unlink_twitter_account'),

    # make uuid note as the last url
    url(r'^([\w-]{30,})/$', 'view_note', name='notes_view_note'),
)

