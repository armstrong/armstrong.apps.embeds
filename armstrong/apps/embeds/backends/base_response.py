from ..models import Type, Provider


class Response(object):
    type_field = 'type'
    provider_field = 'provider_name'

    def __init__(self, data=None, fresh=False):
        self.data = data or {}
        self.fresh = bool(fresh)  # True = new response data from the Backend

    def __eq__(self, other):
        try:
            return self.data == other.data
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self == other

    def is_valid(self):
        raise NotImplementedError()

    def is_fresh(self):
        return self.fresh

    @property
    def type(self):
        if not hasattr(self, '_type'):
            self._type = None
            name = self.data.get(self.type_field)
            if name:
                self._type, _ = Type.objects.get_or_create(name=name)
        return self._type

    @property
    def provider(self):
        if not hasattr(self, '_provider'):
            self._provider = None
            name = self.data.get(self.provider_field)
            if name:
                self._provider, _ = Provider.objects.get_or_create(name=name)
        return self._provider

    #
    # Provide a standard interface for attributes we expect in the response
    # return an empty string by default to prevent "None" leaking in the template
    # though `data` is available, the goal is to avoid accessing it
    #
    def _get(self, attr):
        return self.data.get(attr, '')

    title = property(lambda self: self._get('title'))
    author_name = property(lambda self: self._get('author_name'))
    author_url = property(lambda self: self._get('author_url'))
    image_url = property(lambda self: self._get('thumbnail_url'))
    image_height = property(lambda self: self._get('thumbnail_height'))
    image_width = property(lambda self: self._get('thumbnail_width'))
    render = property(lambda self: self._get('html'))
