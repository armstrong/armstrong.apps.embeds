from django.test import TestCase

from armstrong.apps.embeds.backends.default import DefaultBackend, DefaultResponse
from ._common import CommonBackendTestCaseMixin, CommonResponseTestCaseMixin


class DefaultResponseTestCase(CommonResponseTestCaseMixin, TestCase):
    response_cls = DefaultResponse


class DefaultBackendTestCase(CommonBackendTestCaseMixin, TestCase):
    response_cls = DefaultResponse
    backend_cls = DefaultBackend
    url = "http://www.testme.com/embed?id=123"
    data = dict(url=url)

    def test_backend_response_returns_same_url(self):
        response = self.backend.call(self.url)
        self.assertDictEqual(response._data, self.data)

    def test_response_data(self):
        self._test_response_data(self.url, self.data)
