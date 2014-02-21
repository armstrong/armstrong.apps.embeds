from armstrong.dev.default_settings import *

# KLUDGE: this key is used for testing of the Embedly-Python library
# If it ever becomes invalid, use an API key from a real account (free or paid doesn't matter)
# https://github.com/embedly/embedly-python/blob/b8325fc49396e3b0d10f65847c6cc9fb23bd9482/embedly/tests.py#L11
EMBEDLY_KEY = 'internal'

INSTALLED_APPS.extend([
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.formtools'])

DEBUG = True
STATIC_URL = "/static/"
ROOT_URLCONF = 'armstrong.apps.embeds.tests.embeds_support.urls'
