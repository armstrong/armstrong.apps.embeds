import re
import inspect

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django_extensions.db.fields.json import JSONField
from model_utils.fields import MonitorField

from .backends import get_backend, InvalidResponseError
from .fields import EmbedURLField, EmbedForeignKey


class Backend(models.Model):
    """
    Model representing rendering/data APIs that tell us how to use our
    Embed objects. We can programatically assign APIs to Embed objects
    so we can control and define how they are rendered. Also allow
    prioritization of APIs to provide fallback rendering options.

    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(
                unique=True,
                max_length=50,
                help_text="Used to lookup the actual Backend code. Changing this in the database requires changes in the code.")
    description = models.CharField(max_length=255, null=True, blank=True)
    regex = models.CharField(
                max_length=100,
                help_text="Used to match a URL when automatically assigning backends.")
    priority = models.PositiveSmallIntegerField(
                default=1,
                help_text="A higher number means higher priority. Used when automatically assigning a backend.")

    def __unicode__(self):
        return "%s (priority: %i; regex: %s)" \
            % (self.name, self.priority, self.regex)

    def __init__(self, *args, **kwargs):
        super(Backend, self).__init__(*args, **kwargs)

        # Load the backend code and sanity check
        try:
            self._backend = get_backend(self.slug)
        except ImportError as e:
            raise ImproperlyConfigured('Backends must have a code module: %s' % e)

        # Ease of use: passthrough methods to the backend API for transparency to the calling code
        self._proxy_to_backend = []
        for name, method in inspect.getmembers(self._backend, inspect.ismethod):
            if hasattr(method, 'proxy') and method.proxy:
                self._proxy_to_backend.append(name)

    def __getattr__(self, name):
        if name in self._proxy_to_backend:
            return getattr(self._backend, name)
        return object.__getattribute__(self, name)


class Provider(models.Model):
    """Normalize the embed resource provider"""

    name = models.CharField(
            max_length=50,
            unique=True,
            editable=False,
            help_text="Automatically populated by the backends")

    def __unicode__(self):
        return u"%s" % self.name


class Type(models.Model):
    """Normalize the embed resource type"""

    name = models.CharField(
            max_length=25,
            unique=True,
            editable=False,
            help_text="Automatically populated by the backends")

    def __unicode__(self):
        return u"%s" % self.name


class Embed(models.Model):
    """
    A URL represented by a Backend that provides the interface for
    interacting with and extracting metadata from the external content.

    """
    url = EmbedURLField(unique=True, response_field='response', assign_func="_auto_assign_backend")
    backend = EmbedForeignKey(Backend, response_field='response')

    # Populated from the actual response
    _response = None
    type = models.ForeignKey(Type, null=True, blank=True)
    provider = models.ForeignKey(Provider, null=True, blank=True)
    response_cache = JSONField()
    response_last_updated = MonitorField(default=None, null=True, blank=True, monitor='response_cache')

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        """
        Build out this Embed from a Response object
        If the Response is valid and fresh, populate the object metadata.
        The fresh determination is mainly used when reconstructing this
        from the database where we need to rebuild the Response object
        but there is no need to re-write the metadata.

        """
        from .backends.base_response import Response
        if not isinstance(response, Response):
            raise InvalidResponseError("not a Response object")

        if self.response == response:
            return  # ignore attempts to set the same response

        self._response = response  # wrapped Response object
        if response.is_valid() and response.is_fresh():
            self.type = response.type
            self.provider = response.provider
            self.response_cache = response._data

    @response.deleter
    def response(self):
        """Clear everything that depends on the Response data"""

        self._response = None
        self.type = None
        self.provider = None
        self.response_cache = None

    def get_response(self):
        """Retrieve a new response from the Backend"""
        return self.backend.call(self.url)

    def update_response(self):
        """
        Get a fresh response from the Backend and update
        if it's valid and different from what we already have.

        """
        new_response = self.get_response()
        if new_response and new_response.is_valid() and new_response != self.response:
            self.response = new_response
            return True
        return False

    def __unicode__(self):
        val = self.url if self.url else self.pk if self.pk else "new"
        return u"Embed-%s" % val

    def __init__(self, *args, **kwargs):
        super(Embed, self).__init__(*args, **kwargs)

        if self.response_cache:
            self.response = self.backend.wrap_response_data(self.response_cache)

    def save(self, *args, **kwargs):
        """Try to get a response for new objects so we can save it as well"""

        if not self.pk and not self.response:
            try:
                self.update_response()
            except InvalidResponseError:
                pass
        super(Embed, self).save(*args, **kwargs)

    def _auto_assign_backend(self):
        """New objects without a backend are automatically assigned one"""

        # Due to the nature of ForeignKeys, use hasattr() instead of getattr()
        if self.url and not self.pk and not hasattr(self, 'backend'):
            for backend in Backend.objects.all().order_by('-priority'):
                if re.search(backend.regex, self.url):
                    self.backend = backend
                    break


# HACK - We have a version of this issue where the backend ForeignKey relationship isn't
# fully hooked up and save() fails. It only happens when the backend is assigned during
# __init__(). To workaround, we register a signal to fix the pointer after init is complete.
# http://stackoverflow.com/questions/13248994/django-assigning-foreign-key-before-target-model-is-saved
def _assign_backend_hack(sender, instance, **kwargs):
    # Due to the nature of ForeignKeys, use hasattr() instead of getattr()
    if hasattr(instance, 'backend'):
        instance.backend = instance.backend
models.signals.post_init.connect(_assign_backend_hack, sender=Embed)
