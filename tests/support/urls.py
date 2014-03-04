from django.contrib import admin

try:
    from django.conf.urls import patterns, include
except ImportError:  # Django 1.3 # pragma: no cover
    from django.conf.urls.defaults import patterns, include


admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)


# for shell & runserver: Django 1.3 and 1.4 don't need this, but 1.5 does
# it will only work if DEBUG is True
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
