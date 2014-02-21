import fudge
from datetime import datetime, timedelta

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from armstrong.apps.embeds.models import Embed, Backend, EmbedType, Provider
from armstrong.apps.embeds.backends import InvalidResponseError, proxy
from armstrong.apps.embeds.backends.default import DefaultBackend, DefaultResponse
from .mixins import TemplateCompareTestMixin


def fake_backend_init(obj, *args, **kwargs):
    """Don't error on non-unique slug field"""

    from ..backends import get_backend
    super(Backend, obj).__init__(*args, **kwargs)
    obj._backend = get_backend('default')  # patching this part
    obj._setup_backend_proxy_methods()


class BackendModelTestCase(TestCase):
    def setUp(self):
        self.url = "http://www.testme.com"
        self.data = dict(url=self.url)
        self.backend_cls = DefaultBackend
        self.response_cls = DefaultResponse
        self.backend = Backend(slug='default')

    def test_empty_model_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            Backend()

    def test_fake_model_slug_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            Backend(slug='fake')

    def test_model_inits_properly(self):
        self.assertTrue(isinstance(self.backend._backend, self.backend_cls))

    def test_model_proxys_properly(self):
        for method_name in self.backend._proxy_to_backend:
            self.assertEqual(
                getattr(self.backend, method_name).im_self,
                self.backend._backend)

    def test_using_proxy_decorator(self):
        class Stub(self.backend_cls):
            proxy_me = proxy(lambda _: "made it here")
            but_not_me = lambda _: "unseen"

        self.backend._backend = Stub()
        self.backend._setup_backend_proxy_methods()

        self.assertEqual(self.backend.proxy_me(), "made it here")
        with self.assertRaises(AttributeError):
            self.backend.but_not_me()

    def test_model_calls_properly(self):
        response = self.backend.call(self.url)
        self.assertTrue(isinstance(response, self.response_cls))

    def test_model_wraps_data_properly(self):
        wrapped = self.backend.wrap_response_data(self.data)
        self.assertTrue(isinstance(wrapped, self.response_cls))
        self.assertDictEqual(wrapped._data, self.data)

    def test_wrapped_response_equals_original_response(self):
        response = self.backend.call(self.url)
        wrapped = self.backend.wrap_response_data(response._data)
        self.assertDictEqual(response._data, wrapped._data)


class EmbedTypeTestCase(TestCase):
    def test_new_object_auto_sets_slug_on_save(self):
        new = EmbedType.objects.create(name="Test this slug")
        self.assertEqual(new.slug, "test-this-slug")


class EmbedModelTestCase(TestCase):
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
        self.assertIsNone(embed._response)
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

    def test_embed_requires_backend(self):
        e = Embed()
        with self.assertRaises(ValueError):
            e.save()

    def test_backend_autoassigns_on_save(self):
        e = Embed(url=self.url)
        e.save()
        self.assertTrue(hasattr(e, "backend"))
        self.assertTrue(isinstance(e.backend, Backend))
        self.assertTrue(isinstance(e.backend._backend, self.backend_cls))

    def test_choose_backend_returns_none_when_there_is_no_url(self):
        e = Embed()
        self.assertIsNone(e.choose_backend())

    def test_choose_backend_works_with_passed_url(self):
        e = Embed()
        self.assertEqual(e.choose_backend(self.url), self.backend)

    def test_choose_backend_returns_none_when_there_are_no_backends(self):
        Backend.objects.all().delete()
        e = Embed(url=self.url)
        self.assertIsNone(e.choose_backend())

    def test_choose_backend(self):
        e = Embed(url=self.url)
        b = e.choose_backend()
        self.assertTrue(isinstance(b, Backend))
        self.assertTrue(isinstance(b._backend, self.backend_cls))
        self.assertEqual(b, self.backend)

    def test_choose_backend_gets_higher_priority_option(self):
        e = Embed(url=self.url)

        with fudge.patched_context(Backend, '__init__', fake_backend_init):
            b1 = Backend.objects.create(name='b1', slug='b1', regex='.*', priority=5)
            self.assertEqual(e.choose_backend(), b1)
            b2 = Backend.objects.create(name='b2', slug='b2', regex='.*', priority=6)
            self.assertEqual(e.choose_backend(), b2)

    def test_choose_backend_skips_non_matching_regex(self):
        e = Embed(url=self.url)

        with fudge.patched_context(Backend, '__init__', fake_backend_init):
            Backend.objects.create(name='b1', slug='b1', regex='thiswontmatch', priority=5)
            self.assertEqual(e.choose_backend(), self.backend)

    def test_choose_backend_returns_none_without_matching_regex(self):
        self.backend.regex = "thiswontmatch"
        self.backend.save()

        e = Embed(url=self.url)
        self.assertIsNone(e.choose_backend())

    def test_backend_cant_auto_assign_when_there_are_no_backends(self):
        Backend.objects.all().delete()
        e = Embed(url=self.url)
        with self.assertRaises(ValueError):
            e.save()

    def test_empty_embed_doesnt_have_response_data(self):
        e = Embed()
        self.expect_empty_response_data(e)

    def test_response_must_be_a_response_object(self):
        e = Embed()
        with self.assertRaises(InvalidResponseError):
            e.response = None

        with self.assertRaises(InvalidResponseError):
            e.response = "this should break"

    def test_response_can_be_invalid(self):
        class CustomResponse(self.response_cls):
            def is_valid(self):
                return False

        e = Embed()
        e.response = CustomResponse()
        self.assertTrue(isinstance(e.response, CustomResponse))

    def test_wont_assign_duplicate_response(self):
        e = Embed()
        r1 = self.response_cls(dict(a=1))
        r2 = self.backend.wrap_response_data(dict(a=1))
        e.response = r1
        self.assertEqual(id(r1), id(e.response))
        e.response = r2
        self.assertEqual(id(r1), id(e.response))

    def test_get_response_requires_backend(self):
        with self.assertRaises(Backend.DoesNotExist):
            Embed().get_response()

    def test_get_response_without_url_returns_none(self):
        e = Embed(backend=self.backend)
        self.assertIsNone(e.get_response())

    def test_get_response_returns_correct_response(self):
        e = Embed(url=self.url, backend=self.backend)
        response = e.get_response()
        self.assertTrue(isinstance(response, self.response_cls))
        self.assertEqual(response._data['url'], self.url)

    def test_get_response_returns_same_as_direct_call(self):
        e = Embed(url=self.url, backend=self.backend)
        self.assertEqual(e.get_response(), self.backend.call(self.url))

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
        t = EmbedType.objects.create(name='different')
        p = Provider.objects.create(name='different')
        d = {'key': 'value'}

        e = Embed(url=self.url, backend=self.backend, type=t, provider=p, response_cache=d)
        self.response._fresh = False
        e.response = self.response

        self.assertIs(e.type, t)
        self.assertIs(e.provider, p)
        self.assertEqual(e.response_cache, d)

    def test_invalid_response_doesnt_set_properties(self):
        class CustomResponse(self.response_cls):
            def is_valid(self):
                return False

        self.response.__class__ = CustomResponse
        self.assertFalse(self.response.is_valid())

        e = Embed()
        e.response = self.response
        self.assertIsNone(e.type)
        self.assertIsNone(e.provider)
        self.assertEqual(e.response_cache, {})

    def test_invalid_response_doesnt_alter_properties(self):
        class CustomResponse(self.response_cls):
            def is_valid(self):
                return False

        self.response.__class__ = CustomResponse
        self.assertFalse(self.response.is_valid())

        t = EmbedType.objects.create(name='different')
        p = Provider.objects.create(name='different')
        d = {'key': 'value'}

        e = Embed(url=self.url, backend=self.backend, type=t, provider=p, response_cache=d)
        e.response = self.response

        self.assertIs(e.type, t)
        self.assertIs(e.provider, p)
        self.assertEqual(e.response_cache, d)

    def test_response_cache_requires_backend(self):
        with self.assertRaises(Backend.DoesNotExist):
            Embed(response_cache=dict(a=2))

    def test_response_cache_wraps_correctly(self):
        data = dict(a=2)
        e = Embed(response_cache=data, backend=self.backend)

        self.assertDictEqual(e.response_cache, data)
        self.assertDictEqual(e.response._data, data)
        self.assertEqual(e.response, self.response_cls(data))

    def test_wrapped_response_doesnt_update(self):
        data = dict(url=self.url)
        e = Embed(url=self.url, response_cache=data, backend=self.backend)
        self.assertFalse(e.update_response())

    def test_update_requires_backend(self):
        with self.assertRaises(Backend.DoesNotExist):
            Embed().update_response()

    def test_update_is_false_without_url(self):
        e = Embed(backend=self.backend)
        self.assertFalse(e.update_response())

    def test_new_response_updates(self):
        e = Embed(url=self.url, backend=self.backend)
        self.assertTrue(e.update_response())

    def test_same_response_doesnt_update(self):
        e = Embed(url=self.url, backend=self.backend)
        e.response = self.response_cls(dict(url=self.url))
        self.assertFalse(e.update_response())

    def test_duplicate_update_doesnt_update(self):
        e = Embed(url=self.url, backend=self.backend)
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

    def test_new_embed_doesnt_have_to_create_response_on_save(self):
        def raise_exec(obj):
            raise InvalidResponseError

        e = Embed(url=self.url)
        self.assertIsNone(e.response)

        with fudge.patched_context(Embed, 'update_response', raise_exec):
            e.save()
            self.assertIsNone(e.response)

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

    def test_changing_backend_clears_response_data(self):
        e = Embed(backend=self.backend)
        e.response = self.response
        self.assertIsNotNone(e.response)

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


class EmbedModelLayoutTestCase(TemplateCompareTestMixin, TestCase):
    fixtures = ['embed_backends']

    def setUp(self):
        # Remove everything but the default Backend
        Backend.objects.exclude(slug="default").delete()

        self.embed = Embed(
            url="http://www.testme.com",
            backend=Backend.objects.get(slug='default'))
        self.tpl_name = "tpl"
        self.type_name = EmbedType()._meta.object_name.lower()
        self.type_slug = "photo"

    def test_no_backend_uses_fallback_template(self):
        e = Embed(url="http://www.testme.com")
        self.assertFalse(hasattr(e, 'backend'))

        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(e, expected, use_fallback=True)

    def test_valid_response_without_a_type(self):
        self.embed.update_response()

        self.assertTrue(self.embed.response.is_valid())
        self.assertIsNone(self.embed.type)

        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(self.embed, expected)

    def test_invalid_response_without_a_type_uses_fallback(self):
        response = self.embed.get_response()
        response.is_valid = lambda: False
        self.embed.response = response

        self.assertFalse(self.embed.response.is_valid())
        self.assertIsNone(self.embed.type)

        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(self.embed, expected, use_fallback=True)

    def test_invalid_response_with_a_type_uses_fallback(self):
        response = self.embed.get_response()
        response.is_valid = lambda: False
        self.embed.response = response
        self.embed.type = EmbedType(slug=self.type_slug)

        self.assertFalse(self.embed.response.is_valid())

        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(self.embed, expected, use_fallback=True, use_type=True)

    def test_valid_response_with_a_type(self):
        self.embed.update_response()
        self.embed.type = EmbedType(slug=self.type_slug)

        self.assertTrue(self.embed.response.is_valid())

        expected = [
            '%(base)s/%(app)s/%(typemodel)s/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(self.embed, expected, use_type=True)
