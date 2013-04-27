from django.test import TestCase as DjangoTestCase

from armstrong.apps.embeds.backends.base_response import *


__all__ = ['ResponseTestCase']


class ResponseTestCase(DjangoTestCase):
    def test_empty_responses_are_equal(self):
        self.assertEqual(Response(), Response())

    def test_responses_are_equal(self):
        self.assertEqual(Response({'data': 1}), Response({'data': 1}))

    def test_empty_response_is_not_equal(self):
        self.assertNotEqual(Response({'data': 1}), Response())

    def test_responses_are_not_equal(self):
        self.assertNotEqual(Response({'data': 1}), Response({'data': 2}))

    def test_is_valid_is_not_implemented(self):
        self.assertRaises(NotImplementedError, Response().is_valid)

    def test_is_valid_is_implemented(self):
        class CustomResponse(Response):
            def is_valid(self):
                return True
        self.assertTrue(CustomResponse().is_valid())

    def test_is_fresh(self):
        self.assertTrue(Response({}, True).is_fresh())

    def test_is_not_fresh(self):
        self.assertFalse(Response().is_fresh())

    def test_empty_data_returns_empty_type(self):
        self.assertEqual(Response().type, None)

    def test_empty_data_returns_empty_provider(self):
        self.assertEqual(Response().provider, None)

    def test_empty_data_does_not_create_type(self):
        Response().type
        self.assertFalse(Type.objects.exists())

    def test_empty_data_does_not_create_provider(self):
        Response().provider
        self.assertFalse(Provider.objects.exists())

    def test_creates_type(self):
        r = Response({'type': 'TestType'})
        self.assertTrue(isinstance(r.type, Type))
        self.assertEqual(r.type.name, 'TestType')
        self.assertEqual(Type.objects.count(), 1)

    def test_creates_provider(self):
        r = Response({'provider_name': 'TestProvider'})
        self.assertTrue(isinstance(r.provider, Provider))
        self.assertEqual(r.provider.name, 'TestProvider')
        self.assertEqual(Provider.objects.count(), 1)

    def test_creates_type_from_custom_type_field(self):
        class CustomResponse(Response):
            type_field = "custom"

        r = CustomResponse({'custom': 'TestType'})
        self.assertTrue(isinstance(r.type, Type))
        self.assertEqual(r.type.name, 'TestType')
        self.assertEqual(Type.objects.count(), 1)

    def test_creates_provider_from_custom_provider_field(self):
        class CustomResponse(Response):
            provider_field = "custom"

        r = CustomResponse({'custom': 'TestProvider'})
        self.assertTrue(isinstance(r.provider, Provider))
        self.assertEqual(r.provider.name, 'TestProvider')
        self.assertEqual(Provider.objects.count(), 1)

    def test_missing_data_returns_empty_string(self):
        self.assertEqual(Response().title, '')
        self.assertEqual(Response().render, '')

    def test_missing_attr_raises_error(self):
        with self.assertRaises(AttributeError):
            Response().fake

    def test_missing_data_attr_raises_error(self):
        with self.assertRaises(KeyError):
            Response().data['fake']

    def test_data_getter_returns_empty_on_missing_attr(self):
        r = Response()
        self.assertEqual(r._get('fake'), '')

    def test_data_is_correct(self):
        r = Response(dict(title='Title', html='<iframe>'))
        self.assertEqual(r.title, 'Title')
        self.assertEqual(r.render, '<iframe>')
