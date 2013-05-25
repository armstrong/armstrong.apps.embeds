from . import proxy
from .base_response import Response


class DefaultResponse(Response):
    def is_valid(self):
        return True


class DefaultBackend(object):
    "Use the only thing we can count on - the `url`"
    response_class = DefaultResponse

    @proxy
    def call(self, url):
        if not url:
            return None
        return self.wrap_response_data({'url': url}, fresh=True)

    @proxy
    def wrap_response_data(self, data, **kwargs):
        return self.response_class(data, **kwargs)
