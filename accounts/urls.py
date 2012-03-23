from django.conf.urls import patterns, url

urlpatterns = patterns('kindleio.accounts.views',
    url(r'^login/$', 'site_login', name='accounts_login'),
    url(r'^signup/$', 'signup', name='accounts_signup'),
    url(r'^password_reset/$', 'password_reset', name='accounts_password_reset'),
    url(r'^logout/$', 'site_logout', name='accounts_logout'),
    url(r'^profile/$', 'profile', name='accounts_profile'),

    url(r'^login_with_douban/$', 'login_with_douban', name="login_with_douban"),
    url(r'^douban_callback/$', 'douban_callback', name="douban_callback"),
    url(r'^login_with_twitter/$', 'login_with_twitter', name="login_with_twitter"),
    url(r'^twitter_callback/$', 'twitter_callback', name="twitter_callback"),
)

