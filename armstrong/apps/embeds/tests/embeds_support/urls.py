from django.contrib import admin

try:
    from django.conf.urls import patterns, include
except ImportError:  # Django 1.3
    from django.conf.urls.defaults import patterns, include


admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)
