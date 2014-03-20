from __future__ import absolute_import
from django.conf import settings
from embedly import Embedly as EmbedlyAPI
from httplib2 import ServerNotFoundError

from .. import logger
from . import proxy, InvalidResponseError
from .base_response import BaseResponse


class EmbedlyResponse(BaseResponse):
    def is_valid(self):
        return not (
            not self._data or
            self._data.get('error') or
            self._data.get('type', '') == 'error')

    #
    # Data attribute interface
    #
    def _get_by_type(self, attr_by_type):
        if not self.type:
            return ''
        attr_name = attr_by_type.get(self.type.name.lower())
        return self._get(attr_name)

    @property
    def image_url(self):
        return self._get_by_type(dict(
            photo='url',
            link='thumbnail_url',
            video='thumbnail_url'))

    @property
    def image_height(self):
        return self._get_by_type(dict(
            photo='height',
            link='thumbnail_height',
            video='thumbnail_height'))

    @property
    def image_width(self):
        return self._get_by_type(dict(
            photo='width',
            link='thumbnail_width',
            video='thumbnail_width'))


class EmbedlyBackend(object):
    """
    The response object from oembed() is a dict that should look like this:
        response.__dict__ ->
        {'data': {'type': 'error', 'error_code': 400, 'error': True}, 'method': 'oembed', 'original_url': 'bad_url'}
        - or -
        {'data': {u'provider_url': u'http://vimeo.com/', u'description': ...}, 'method': 'oembed', 'original_url': 'http://vimeo.com/1111'}

    """
    response_class = EmbedlyResponse

    def __init__(self):
        try:
            key = getattr(settings, 'EMBEDLY_KEY')
        except AttributeError:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(
                '%s requires an API key be specified in settings' %
                type(self).__name__)
        self.client = EmbedlyAPI(key)

    @proxy
    def call(self, url):
        if not url:
            return None

        logger.debug("Embedly call to oembed('%s')" % url)
        try:
            response = self.client.oembed(url)
        except ServerNotFoundError:
            #PY3 use PEP 3134 exception chaining
            import sys
            exc_cls, msg, trace = sys.exc_info()
            raise (InvalidResponseError,
                   "%s: %s" % (exc_cls.__name__, msg),
                   trace)

        response = self.wrap_response_data(
            getattr(response, 'data', None), fresh=True)
        if not response.is_valid():
            logger.warn("%s error: %s" %
                        (type(response).__name__, response._data))
        return response

    @proxy
    def wrap_response_data(self, data, **kwargs):
        return self.response_class(data, **kwargs)
