import re
import inspect

from django.db import models
from django.template.defaultfilters import slugify
from django.core.exceptions import ImproperlyConfigured
from django_extensions.db.fields.json import JSONField
from model_utils.fields import MonitorField

from .backends import get_backend, InvalidResponseError
from .fields import EmbedURLField, EmbedForeignKey
from .mixins import TemplatesByEmbedTypeMixin


class Backend(models.Model):
    """
    Model representing rendering/data APIs that tell us how to use our
    Embed objects. We can programatically assign APIs to Embed objects
    so we can control and define how they are rendered. Also allow
    prioritization of APIs to provide fallback rendering options.

    """
    name = models.CharField(max_length=50)
    code_path = models.CharField(
                unique=True,
                max_length=100,
                help_text="Full Python path for the actual Backend code.")
    description = models.CharField(max_length=255, null=True, blank=True)
    regex = models.CharField(
                max_length=100,
                help_text="Used to match a URL when automatically assigning backends.")
    priority = models.PositiveSmallIntegerField(
                default=1,
                help_text="A higher number means higher priority. Used when automatically assigning a backend.")

    def __unicode__(self):
        return u"%s (priority: %i; regex: %s)" \
            % (self.name, self.priority, self.regex)

    def _setup_backend_proxy_methods(self):
        """Ease of use: passthrough methods to the backend API for transparency to the calling code"""

        self._proxy_to_backend = []
        for name, method in inspect.getmembers(self._backend, inspect.ismethod):
            if hasattr(method, 'proxy') and method.proxy:
                self._proxy_to_backend.append(name)

    def __init__(self, *args, **kwargs):
        super(Backend, self).__init__(*args, **kwargs)

        # Load the backend code and sanity check
        try:
            self._backend = get_backend(self.code_path)
        except ImportError as e:
            raise ImproperlyConfigured('Backends must have a code module: %s' % e)

        self._setup_backend_proxy_methods()

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


class EmbedType(models.Model):
    """Normalize the embed resource type"""

    name = models.CharField(
            max_length=25,
            unique=True,
            editable=False,
            help_text="Automatically populated by the backends")
    slug = models.SlugField(
            max_length=25,
            unique=True,
            editable=False,
            help_text="Used as a folder name in the template lookup.")

    def __unicode__(self):
        return u"%s" % self.name

    def save(self, *args, **kwargs):
        """Auto-assign a slug for new objects"""

        if not self.pk and not self.slug:
            self.slug = slugify(self.name)
        super(EmbedType, self).save(*args, **kwargs)


class Embed(models.Model, TemplatesByEmbedTypeMixin):
    """
    A URL represented by a Backend that provides the interface for
    interacting with and extracting metadata from the external content.

    """
    url = EmbedURLField(unique=True, response_attr='response')
    backend = EmbedForeignKey(Backend, blank=True, response_attr='response',
        help_text="The most appropriate Backend will auto-assign if not explicitly provided")

    # Populated from the actual response
    _response = None
    type = models.ForeignKey(EmbedType, null=True, blank=True)
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

    def choose_backend(self, url=None):
        """Determine the best Backend to use for this object's URL"""

        if not (self.url or url):
            return None

        for backend in Backend.objects.all().order_by('-priority'):
            if re.search(backend.regex, self.url or url):
                return backend
        return None

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
        """Auto-assign a Backend and try to load response data for new Embeds"""

        if not self.pk:
            # Due to the nature of ForeignKeys, use hasattr() instead of getattr()
            if not hasattr(self, 'backend'):
                self.backend = self.choose_backend()

            if not self.response:
                try:
                    self.update_response()
                except InvalidResponseError:
                    pass
        super(Embed, self).save(*args, **kwargs)
