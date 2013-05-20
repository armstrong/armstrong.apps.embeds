import inspect
from functools import wraps
from abc import ABCMeta, abstractproperty

from armstrong.apps.embeds.models import Provider, Type
from armstrong.apps.embeds.backends import get_backend


class CommonResponseTestCaseMixin(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def response_cls(self):
        return self.response_cls

    def test_empty_responses_are_equal(self):
        self.assertEqual(self.response_cls(), self.response_cls())

    def test_responses_are_equal(self):
        self.assertEqual(self.response_cls({'data': 1}), self.response_cls({'data': 1}))

    def test_empty_response_is_not_equal(self):
        self.assertNotEqual(self.response_cls({'data': 1}), self.response_cls())

    def test_responses_are_not_equal(self):
        self.assertNotEqual(self.response_cls({'data': 1}), self.response_cls({'data': 2}))

    def test_is_fresh(self):
        self.assertTrue(self.response_cls({}, True).is_fresh())

    def test_is_not_fresh(self):
        self.assertFalse(self.response_cls().is_fresh())

    def test_empty_data_returns_empty_type(self):
        self.assertEqual(self.response_cls().type, None)

    def test_empty_data_returns_empty_provider(self):
        self.assertEqual(self.response_cls().provider, None)

    def test_empty_data_does_not_create_type(self):
        self.response_cls().type
        self.assertFalse(Type.objects.exists())

    def test_empty_data_does_not_create_provider(self):
        self.response_cls().provider
        self.assertFalse(Provider.objects.exists())

    def test_creates_type(self):
        r = self.response_cls({'type': 'TestType'})
        self.assertTrue(isinstance(r.type, Type))
        self.assertEqual(r.type.name, 'TestType')
        self.assertEqual(Type.objects.count(), 1)

    def test_creates_provider(self):
        r = self.response_cls({'provider_name': 'TestProvider'})
        self.assertTrue(isinstance(r.provider, Provider))
        self.assertEqual(r.provider.name, 'TestProvider')
        self.assertEqual(Provider.objects.count(), 1)

    def test_creates_type_from_custom_type_field(self):
        class CustomResponse(self.response_cls):
            _type_field = "custom"

        r = CustomResponse({'custom': 'TestType'})
        self.assertTrue(isinstance(r.type, Type))
        self.assertEqual(r.type.name, 'TestType')
        self.assertEqual(Type.objects.count(), 1)

    def test_creates_provider_from_custom_provider_field(self):
        class CustomResponse(self.response_cls):
            _provider_field = "custom"

        r = CustomResponse({'custom': 'TestProvider'})
        self.assertTrue(isinstance(r.provider, Provider))
        self.assertEqual(r.provider.name, 'TestProvider')
        self.assertEqual(Provider.objects.count(), 1)

    def test_missing_data_returns_empty_string(self):
        self.assertEqual(self.response_cls().title, '')
        self.assertEqual(self.response_cls().render, '')

    def test_missing_attr_raises_error(self):
        with self.assertRaises(AttributeError):
            self.response_cls().fake

    def test_missing_data_attr_raises_error(self):
        with self.assertRaises(KeyError):
            self.response_cls()._data['fake']

    def test_data_getter_returns_empty_on_missing_attr(self):
        r = self.response_cls()
        self.assertEqual(r._get('fake'), '')

    def test_data_is_correct(self):
        r = self.response_cls(dict(title='Title', html='<iframe>'))
        self.assertEqual(r.title, 'Title')
        self.assertEqual(r.render, '<iframe>')

    def test_invalid_data_is_invalid(self):
        for data in getattr(self, 'invalid_data', []):
            response = self.response_cls(data)
            self.assertFalse(response.is_valid())


class CommonBackendTestCaseMixin(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def response_cls(self):
        return self.response_cls

    @abstractproperty
    def backend_cls(self):
        return self.backend_cls

    @abstractproperty
    def url(self):
        return self.url

    @abstractproperty
    def data(self):
        return self.data

    def setUp(self):
        self.backend = self.backend_cls()

    def _get_backend_name(self):
        name = self.backend_cls.__name__
        return name[:name.rfind('Backend')]

    def test_can_load_backend(self):
        b = get_backend(self._get_backend_name())
        self.assertTrue(isinstance(b, self.backend_cls))

    def test_can_load_backend_by_capitalized_name(self):
        b = get_backend(self._get_backend_name().title())
        self.assertTrue(isinstance(b, self.backend_cls))

    def test_call_requires_url(self):
        with self.assertRaises(TypeError):
            self.backend.call()

    def test_call_returns_response_data(self):
        response = self.backend.call(self.url)
        self.assertTrue(isinstance(response, self.response_cls))
        self.assertTrue(response.is_valid())
        self.assertTrue(response.is_fresh())

    def test_wraps_response_data(self):
        response = self.backend.call(self.url)
        wrapped = self.backend.wrap_response_data(response._data)
        self.assertTrue(isinstance(wrapped, self.response_cls))
        self.assertTrue(wrapped.is_valid())
        self.assertFalse(wrapped.is_fresh())

    def test_wrapped_response_equals_original_response(self):
        response = self.backend.call(self.url)
        wrapped = self.backend.wrap_response_data(response._data)
        self.assertDictEqual(response._data, wrapped._data)

    def test_call_for_bad_url_returns_error(self):
        if hasattr(self, 'bad_url'):
            response = self.backend.call(self.bad_url)
            self.assertFalse(response.is_valid())

    def _test_response_data(self, url, data):
        """
        This is a heavy lifter. It'll look at all the 'data' elements of the
        wrapped expected response data (i.e. not methods or private attrs) and
        if we've provided test data, it'll compare it with the real response.

        """
        response = self.backend.call(url)
        expected_response = self.response_cls(data)

        # only examine test data; the real response could have additional data
        for key, value in inspect.getmembers(expected_response):
            if not key.startswith('_') and value and not inspect.ismethod(value):
                response_value = getattr(response, key)
                error_msg = "Failed on <%s>: <%s> != <%s>" % (key, value, response_value)
                self.assertEqual(value, response_value, error_msg)

    def _test_garbage_data_should_not_match_a_valid_response(self, url, data):
        """Purposely compare bad data with a real response"""

        bad_data = {key: 'garbage' for key in data.keys()}
        with self.assertRaises(AssertionError):
            self._test_response_data(url, bad_data)
