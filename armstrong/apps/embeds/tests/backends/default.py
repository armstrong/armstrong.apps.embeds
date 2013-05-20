from django.test import TestCase as DjangoTestCase

from armstrong.apps.embeds.backends.default import DefaultBackend, DefaultResponse
from ._common import CommonBackendTestCaseMixin, CommonResponseTestCaseMixin


class DefaultResponseTestCase(CommonResponseTestCaseMixin, DjangoTestCase):
    response_cls = DefaultResponse


class DefaultBackendTestCase(CommonBackendTestCaseMixin, DjangoTestCase):
    response_cls = DefaultResponse
    backend_cls = DefaultBackend
    url = "http://www.testme.com/embed?id=123"
    data = dict(url=url)

    def test_backend_response_returns_same_url(self):
        response = self.backend.call(self.url)
        self.assertDictEqual(response._data, self.data)

    def test_response_data(self):
        self._test_response_data(self.url, self.data)
