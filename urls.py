from django.conf import settings
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'kindleio.views.home', name='home'),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'kindleio.views.home', name='home'),
    url(r'^accounts/', include('kindleio.accounts.urls')),
    url(r'^login/$', 'kindleio.accounts.views.site_login', name='site_login'),
    url(r'^logout/$', 'kindleio.accounts.views.site_logout', name='site_logout'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
