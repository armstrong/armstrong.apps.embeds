from datetime import datetime, timedelta

from django.test import TestCase as DjangoTestCase
from django.core.exceptions import ImproperlyConfigured
import fudge

from armstrong.apps.embeds.models import Embed, Backend, Type, Provider
from armstrong.apps.embeds.backends import InvalidResponseError
from armstrong.apps.embeds.backends.default import DefaultBackend, DefaultResponse
from armstrong.apps.embeds.backends.base_response import Response


class BackendModelTestCase(DjangoTestCase):
    def setUp(self):
        self.url = "http://www.testme.com"
        self.data = dict(url=self.url)
        self.backend_cls = DefaultBackend
        self.response_cls = DefaultResponse

    def test_empty_model_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            Backend()

    def test_fake_model_slug_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            Backend(slug='fake')

    def test_model_inits_properly(self):
        b = Backend(slug='default')
        self.assertTrue(isinstance(b._backend, self.backend_cls))

    def test_model_proxys_properly(self):
        b = Backend(slug='default')
        for method_name in b._proxy_to_backend:
            self.assertEqual(getattr(b, method_name).im_self, b._backend)

    def test_model_calls_properly(self):
        b = Backend(slug='default')
        response = b.call(self.url)
        self.assertTrue(isinstance(response, self.response_cls))

    def test_model_wraps_data_properly(self):
        b = Backend(slug='default')
        wrapped = b.wrap_response_data(self.data)
        self.assertTrue(isinstance(wrapped, self.response_cls))
        self.assertDictEqual(wrapped._data, self.data)

    def test_wrapped_response_equals_original_response(self):
        b = Backend(slug='default')
        response = b.call(self.url)
        wrapped = b.wrap_response_data(response._data)
        self.assertDictEqual(response._data, wrapped._data)


class EmbedTestCase(DjangoTestCase):
    fixtures = ['embed_backends']

    def setUp(self):
        # Remove everything but the default Backend
        Backend.objects.exclude(slug="default").delete()

        self.url = "http://www.testme.com"
        self.new_url = "http://newurl.com"
        self.backend = Backend.objects.get(slug='default')
        self.backend_cls = DefaultBackend
        self.response_cls = DefaultResponse
        self.response = self.response_cls(
            fresh=True,
            data=dict(
                a='one', b=2,
                type='TestType',
                provider_name='TestProvider',
                title='TestTitle'))

    def expect_empty_response_data(self, embed):
        self.assertIsNone(embed.response)
        self.assertIsNone(embed.type)
        self.assertIsNone(embed.provider)
        self.assertEqual(embed.response_cache, {})

    def test_unicode_repr(self):
        e = Embed()
        self.assertEqual(e.__unicode__(), "Embed-new")
        e.pk = 40
        self.assertEqual(e.__unicode__(), "Embed-40")
        e.url = self.url
        self.assertEqual(e.__unicode__(), "Embed-%s" % self.url)
        e.response = self.response
        self.assertEqual(e.__unicode__(), "Embed-%s" % self.url)

    def test_empty_embed_has_no_backend(self):
        e = Embed()
        self.assertFalse(hasattr(e, "backend"))
        with self.assertRaises(Backend.DoesNotExist):
            e.backend

    def test_backend_doesnt_auto_assign_when_there_are_no_backends(self):
        Backend.objects.all().delete()
        e = Embed(url=self.url)
        self.assertFalse(hasattr(e, "backend"))
        with self.assertRaises(Backend.DoesNotExist):
            e.backend

    def test_url_on_init_autoassigns_correct_backend(self):
        e = Embed(url=self.url)
        self.assertTrue(hasattr(e, "backend"))
        self.assertTrue(isinstance(e.backend, Backend))
        self.assertTrue(isinstance(e.backend._backend, self.backend_cls))

    def test_url_assigned_autoassigns_correct_backend(self):
        e = Embed()
        e.url = self.url
        self.assertTrue(hasattr(e, "backend"))
        self.assertTrue(isinstance(e.backend, Backend))
        self.assertTrue(isinstance(e.backend._backend, self.backend_cls))

    def test_backend_doesnt_reassign(self):
        e = Embed(url=self.url)
        backend = e.backend._backend
        e.url = self.new_url
        self.assertIs(backend, e.backend._backend)

    def test_backend_doesnt_clear(self):
        e = Embed(url=self.url)
        backend = e.backend._backend
        e.url = None
        self.assertIs(backend, e.backend._backend)
        e.url = ""
        self.assertIs(backend, e.backend._backend)

    def test_empty_embed_doesnt_have_response_data(self):
        e = Embed()
        self.expect_empty_response_data(e)

    def test_response_must_be_a_response_object(self):
        e = Embed()
        with self.assertRaises(InvalidResponseError):
            e.response = None

    def test_response_must_be_a_response_object_2(self):
        e = Embed()
        with self.assertRaises(InvalidResponseError):
            e.response = "this should break"

    def test_invalid_response_raises_error(self):
        class CustomResponse(Response):
            def is_valid(self):
                return False

        e = Embed()
        with self.assertRaises(InvalidResponseError):
            e.response = CustomResponse()

    def test_valid_response_is_assigned(self):
        class CustomResponse(Response):
            def is_valid(self):
                return True

        e = Embed()
        r = CustomResponse()
        e.response = r
        self.assertIs(e.response, r)

    def test_fresh_response_sets_properties(self):
        e = Embed()
        e.response = self.response
        self.assertIsNotNone(e.type)
        self.assertIsNotNone(e.provider)
        self.assertNotEqual(e.response_cache, {})
        self.assertIs(e.type, self.response.type)
        self.assertIs(e.provider, self.response.provider)
        self.assertDictEqual(e.response_cache, self.response._data)

    def test_un_fresh_response_doesnt_set_properties(self):
        e = Embed()
        self.response._fresh = False
        e.response = self.response
        self.assertIsNone(e.type)
        self.assertIsNone(e.provider)
        self.assertEqual(e.response_cache, {})

    def test_un_fresh_response_doesnt_alter_properties(self):
        t = Type.objects.create(name='different')
        p = Provider.objects.create(name='different')
        d = {'key': 'value'}

        e = Embed(url=self.url, type=t, provider=p, response_cache=d)
        self.response._fresh = False
        e.response = self.response

        self.assertIs(e.type, t)
        self.assertIs(e.provider, p)
        self.assertEqual(e.response_cache, d)

    def test_response_cache_requires_backend(self):
        with self.assertRaises(Backend.DoesNotExist):
            Embed(response_cache=dict(a=2))

    def test_response_cache_wraps_correctly(self):
        data = dict(a=2)
        backend = self.backend
        e = Embed(response_cache=data, backend=backend)

        self.assertDictEqual(e.response_cache, data)
        self.assertDictEqual(e.response._data, data)
        self.assertEqual(e.response, self.response_cls(data))

    def test_wrapped_response_doesnt_update(self):
        data = dict(url=self.url)
        backend = self.backend
        e = Embed(url=self.url, response_cache=data, backend=backend)
        self.assertFalse(e.update_response())

    def test_update_requires_backend(self):
        with self.assertRaises(Backend.DoesNotExist):
            Embed().update_response()

    def test_empty_response_updates(self):
        e = Embed(url=self.url)
        self.assertTrue(e.update_response())

    def test_same_response_doesnt_update(self):
        e = Embed(backend=self.backend)
        e.response = self.response_cls(dict(url=''))
        self.assertFalse(e.update_response())

    def test_duplicate_update_doesnt_update(self):
        e = Embed(url=self.url)
        e.update_response()
        self.assertFalse(e.update_response())

    def test_different_response_updates(self):
        data = dict(other='stuff')
        backend = self.backend
        e = Embed(url=self.url, response_cache=data, backend=backend)
        self.assertTrue(e.update_response())

    def test_new_embed_creates_response_on_save(self):
        e = Embed(url=self.url)
        self.assertIsNone(e.response)
        e.save()
        self.assertIsNotNone(e.response)
        self.assertTrue(isinstance(e.response, self.response_cls))

    def test_deleting_response_clears_data(self):
        e = Embed()
        e.response = self.response

        del e.response
        self.expect_empty_response_data(e)

    def test_existing_embed_doesnt_create_response_on_save(self):
        e = Embed(url=self.url)
        e.save()

        del e.response
        e.save()
        self.expect_empty_response_data(e)

    def test_changing_url_clears_response_data(self):
        e = Embed(url=self.url, backend=self.backend)
        e.response = self.response
        self.assertIsNotNone(e.response)

        e.url = self.new_url
        self.expect_empty_response_data(e)

    @fudge.patch('armstrong.apps.embeds.models.Backend')
    def test_changing_backend_clears_response_data(self, FakeBackend):
        e = Embed(backend=self.backend)
        e.response = self.response
        self.assertIsNotNone(e.response)

        def fake_backend_init(obj, *args, **kwargs):
            """Don't error on non-unique slug field"""

            from ..backends import get_backend
            super(Backend, obj).__init__(*args, **kwargs)
            self._backend = get_backend('default')
            self._proxy_to_backend = []

        with fudge.patched_context(Backend, '__init__', fake_backend_init):
            e.backend = Backend(name='new', slug='new', regex='.*')

        self.expect_empty_response_data(e)

    def test_last_updated_field_updates_on_save(self):
        e = Embed(url=self.url)
        self.assertIsNone(e.response_last_updated)
        e.save()
        self.assertIsNotNone(e.response_last_updated)
        self.assertTrue(isinstance(e.response_last_updated, datetime))

    def test_last_updated_field_doesnt_update_without_new_response(self):
        e = Embed(url=self.url)
        e.save()

        # force an obviously different time
        e.response_last_updated = e.response_last_updated - timedelta(days=1)
        dt = e.response_last_updated

        e.update_response()
        e.save()
        self.assertEqual(e.response_last_updated, dt)

    def test_last_updated_field_updates_with_new_response(self):
        e = Embed(url=self.url)
        e.save()

        # force an obviously different time
        e.response_last_updated = e.response_last_updated - timedelta(days=1)
        dt = e.response_last_updated

        e.url = self.new_url
        e.update_response()
        e.save()
        self.assertGreater(e.response_last_updated, dt)
