from ..models import EmbedType, Provider


class BaseResponse(object):
    _type_field = 'type'
    _provider_field = 'provider_name'

    def __init__(self, data=None, fresh=False):
        self._data = data or {}
        self._fresh = bool(fresh)  # True = new response data from the Backend

    def __eq__(self, other):
        try:
            return self._data == other._data
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self == other

    def is_valid(self):
        raise NotImplementedError()  # pragma: no cover

    def is_fresh(self):
        return self._fresh

    @property
    def type(self):
        if not hasattr(self, '_type'):
            self._type = None
            name = self._data.get(self._type_field)
            if name:
                self._type, _ = EmbedType.objects.get_or_create(name=name)
        return self._type

    @property
    def provider(self):
        if not hasattr(self, '_provider'):
            self._provider = None
            name = self._data.get(self._provider_field)
            if name:
                self._provider, _ = Provider.objects.get_or_create(name=name)
        return self._provider

    #
    # Provide a standard interface for attributes we expect in the response.
    # Return an empty string by default to prevent "None" leaking in the
    # template. Though `data` is available, the goal is to avoid accessing it.
    #
    def _get(self, attr):
        return self._data.get(attr, '')

    title = property(lambda self: self._get('title'))
    author_name = property(lambda self: self._get('author_name'))
    author_url = property(lambda self: self._get('author_url'))
    image_url = property(lambda self: self._get('thumbnail_url'))
    image_height = property(lambda self: self._get('thumbnail_height'))
    image_width = property(lambda self: self._get('thumbnail_width'))
    render = property(lambda self: self._get('html'))
