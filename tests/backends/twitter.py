from armstrong.apps.embeds.backends.twitter import TwitterResponse, TwitterBackend, TWITTER_SCRIPT_TAG
from ._common import CommonBackendTestCaseMixin, CommonResponseTestCaseMixin
from .._utils import TestCase


__all__ = ['TwitterResponseTestCase', 'TwitterBackendTestCase']


class TwitterResponseTestCase(CommonResponseTestCaseMixin, TestCase):
    response_cls = TwitterResponse


class TwitterBackendTestCase(CommonBackendTestCaseMixin, TestCase):
    backend_cls = TwitterBackend
    response_cls = TwitterResponse
    url = "https://twitter.com/#!/twitter/status/99530515043983360"
    data = dict(
        type="rich",
        provider_name="Twitter")

    def test_response(self):
        self._test_response_data(self.url, self.data)
        self._test_garbage_data_should_not_match_a_valid_response(self.url, self.data)

    def test_backend_provides_script_tag_as_html_data_value(self):
        response = self.backend.call(self.url)
        expected_result = TWITTER_SCRIPT_TAG % self.url
        self.assertEqual(response.render, expected_result)
