from django.test import TestCase as DjangoTestCase

from armstrong.apps.embeds.backends import get_backend
from armstrong.apps.embeds.backends.default import DefaultBackend, DefaultResponse


__all__ = ['CommonBackendTestCaseMixin', 'DefaultBackendTestCase', 'LoadDefaultBackendTestCase']


class CommonBackendTestCaseMixin(object):
    def setUp(self):
        self.url = "http://www.testme.com/embed?id=123"
        self.data = dict(url=self.url)
        self.response_cls = DefaultResponse

    def test_call_requires_url(self):
        with self.assertRaises(TypeError):
            self.backend.call()

    def test_call_returns_response(self):
        response = self.backend.call(self.url)
        self.assertTrue(isinstance(response, self.response_cls))

    def test_call_returns_fresh_response(self):
        response = self.backend.call(self.url)
        self.assertTrue(response.is_fresh())

    def test_call_returns_valid_response(self):
        response = self.backend.call(self.url)
        self.assertTrue(response.is_valid())

    def test_wraps_data_into_response_class(self):
        response = self.backend.wrap_response_data(self.data)
        self.assertTrue(isinstance(response, self.response_cls))

    def test_wrapped_data_is_valid(self):
        response = self.backend.wrap_response_data(self.data)
        self.assertTrue(response.is_valid())

    def test_wrapped_data_is_not_fresh(self):
        response = self.backend.wrap_response_data(self.data)
        self.assertFalse(response.is_fresh())

    def test_wrapped_response_equals_original_response(self):
        response = self.backend.call(self.url)
        wrapped = self.backend.wrap_response_data(response._data)
        self.assertDictEqual(response._data, wrapped._data)


class LoadDefaultBackendTestCase(DjangoTestCase):
    def test_can_load_backend(self):
        b = get_backend('default')
        self.assertTrue(isinstance(b, DefaultBackend))

    def test_can_load_backend_by_capitalized_name(self):
        b = get_backend('DefAULt')
        self.assertTrue(isinstance(b, DefaultBackend))


class DefaultBackendTestCase(CommonBackendTestCaseMixin, DjangoTestCase):
    def setUp(self):
        self.backend = DefaultBackend()
        super(DefaultBackendTestCase, self).setUp()

    def test_backend_response_returns_same_url(self):
        response = self.backend.call(self.url)
        self.assertDictEqual(response._data, self.data)

    def test_backend_response_returns_empty_data_for_attr(self):
        response = self.backend.call(self.url)
        self.assertEqual(response.title, '')
        self.assertEqual(response.render, '')
