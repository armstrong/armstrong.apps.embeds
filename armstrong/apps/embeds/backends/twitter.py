from . import proxy
from .base_response import BaseResponse


TWITTER_SCRIPT_TAG = '<blockquote class="twitter-tweet">' \
    '<a href="%s"></a></blockquote>' \
    '<script async src="https://platform.twitter.com/widgets.js" ' \
    'charset="utf-8"></script>'


class TwitterResponse(BaseResponse):
    def is_valid(self):
        return True


class TwitterBackend(object):
    """
    The Twitter API v1.1 requires oAuth authentication.
    This backend avoids the API with its restrictions and thus cannot provide
    any metadata or additional information. Instead, this backend wraps the
    given URL in a standard, boilerplate Twitter embed script tag. This works
    to present a render in a template, but that's all it can do.

    """
    response_class = TwitterResponse

    @proxy
    def call(self, url):
        if not url:
            return None

        data = dict(
            type='rich',
            provider_name='Twitter',
            provider_url="https://twitter.com/",
            html=TWITTER_SCRIPT_TAG % url)
        return self.wrap_response_data(data, fresh=True)

    @proxy
    def wrap_response_data(self, data, **kwargs):
        return self.response_class(data, **kwargs)
