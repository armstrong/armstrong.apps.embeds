import fudge
import django
from django.utils import unittest
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission

from armstrong.apps.embeds.models import Backend, Embed
from armstrong.apps.embeds.forms import EmbedForm
from armstrong.apps.embeds.backends import InvalidResponseError, proxy
from armstrong.apps.embeds.backends.default import DefaultResponse, DefaultBackend
from .models import fake_backend_init
from ._utils import TestCase

__all__ = ['EmbedAdminAddTestCase', 'EmbedAdminChangeTestCase',
           'BackendAdminTestCase']


def return_false(obj):
    return False


class CommonAdminBaseTestCase(object):
    fixtures = ['embed_backends.json']

    def setUp(self):
        # create an admin user
        username = 'test'
        pw = 'password'
        self.user = User.objects.create_user(username, 'e@mail.com', pw)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # login
        self.assertTrue(
            self.client.login(username=username, password=pw),
            "Logging in failed.")

    def tearDown(self):
        self.client.logout()

    def test_admin_site_requires_login(self):
        self.client.logout()
        r = self.client.get(self.changelist_url)
        self.assertContains(r, 'Log in')
        self.assertTemplateUsed(r, 'admin/login.html')

    def test_admin_site_requires_permission(self):
        self.user.is_superuser = False
        self.user.save()

        r = self.client.get(self.changelist_url)
        self.assertEqual(r.status_code, 403)


class BackendAdminTestCase(CommonAdminBaseTestCase, TestCase):
    def setUp(self):
        super(BackendAdminTestCase, self).setUp()
        self.add_url = reverse('admin:embeds_backend_add')
        self.changelist_url = reverse('admin:embeds_backend_changelist')
        self.change_url = reverse('admin:embeds_backend_change', args=[1])

    def test_add_page_redirects_to_changelist(self):
        r = self.client.get(self.add_url)
        self.assertRedirects(r, self.changelist_url)

    def test_add_page_displays_message(self):
        msg = 'New Embed backends cannot be added via the Admin'
        r = self.client.get(self.add_url, follow=True)
        self.assertContains(r, msg)

    def test_changelist_page_doesnt_have_add_button(self):
        r = self.client.get(self.changelist_url)
        self.assertTemplateUsed(r, 'embeds/admin/change_list_template.html')
        self.assertNotContains(r, 'href="/admin/embeds/backend/add/"')

    def test_change_page_description_field_uses_textfield(self):
        regex = r'<textarea\s[^>]*id="id_description"\s?[^>]*>'
        r = self.client.get(self.change_url)
        self.assertRegexpMatches(r.content, regex)


class EmbedAdminBaseTestCase(CommonAdminBaseTestCase):
    def setUp(self):
        super(EmbedAdminBaseTestCase, self).setUp()

        # Prepare database contents
        Backend.objects.exclude(name="default").delete()
        self.backend = Backend.objects.get(name='default')
        self.embed = Embed.objects.create(
            url="http://www.github.com/",
            backend=self.backend)
        self.obj_count = Embed.objects.count()

        # other shared vars
        self.add_url = reverse('admin:embeds_embed_add')
        self.changelist_url = reverse('admin:embeds_embed_changelist')
        self.valid_data = dict(url='http://www.fakeurl.com/', backend='')

    def _on_step2(self, test_func, response):
        getattr(self, test_func)(response.context['form'].is_valid())
        getattr(self, test_func)('is_step2' in response.context)
        getattr(self, test_func)('hash_field' in response.context)
        getattr(self, test_func)('hash_value' in response.context)
        getattr(self, test_func)('Preview' in response.context['title'])

    def _prepare_step2_data(self, url, data):
        """
        Post step1 data and prepare the step2 data for final submission
        Return the prepared data and the response from step1.

        """
        r = self.client.post(url, data)
        submit = data
        submit['_save'] = "Save"
        submit['backend'] = 1
        submit[r.context['stage_field']] = 2
        submit[r.context['hash_field']] = r.context['hash_value']
        submit['csrfmiddlewaretoken'] = str(r.context['csrf_token'])
        return submit, r

    def invalid_response_strings(self, response):
        self.assertContains(response,
            "The response for this Embed is invalid. Here's the error data:")
        self.assertContains(response,
            "You can still save this Embed but it won't be very useful without response data.")
        self.assertContains(response,
            "Invalid response from the Backend API")

    def test_empty_url_fails(self):
        data = dict(url='')
        r = self.client.post(self.url, data)
        self.assertFormError(r, 'form', 'url', 'This field is required.')

    def test_invalid_url_fails(self):
        data = dict(url='fake')
        r = self.client.post(self.url, data)
        self.assertFormError(r, 'form', 'url', 'Enter a valid URL.')

    def test_backend_is_not_required(self):
        r = self.client.get(self.url)
        self.assertFalse(r.context['form'].fields['backend'].required)

    def test_backend_can_be_empty(self):
        r = self.client.post(self.url, self.valid_data)
        self.assertEqual(
            r.context['form'].instance.backend,
            self.backend)

    def test_choosen_backend_doesnt_auto_assign(self):
        with fudge.patched_context(Backend, '__init__', fake_backend_init):
            Backend.objects.create(name='b1', code_path='b1', regex='.*', priority=5)

            data = dict(url='www.fakeurl.com', backend=1)
            r = self.client.post(self.url, data)
            self.assertEqual(
                r.context['form'].instance.backend,
                self.backend)

    def test_failed_form_remains_on_step1(self):
        with fudge.patched_context(EmbedForm, 'is_valid', return_false):
            r = self.client.post(self.url, self.valid_data)
            self._on_step2('assertFalse', r)

    def test_valid_form_moves_to_step2(self):
        r = self.client.post(self.url, self.valid_data)
        self._on_step2('assertTrue', r)

    def test_failed_form_on_step2_goes_back_to_step1(self):
        submit, _ = self._prepare_step2_data(self.url, self.valid_data)
        submit['url'] = ''  # bad data

        r = self.client.post(self.url, submit)
        self._on_step2('assertFalse', r)

    def test_step2_has_response_data(self):
        r = self.client.post(self.url, self.valid_data)
        self.assertContains(r, 'Response Data')

    def test_step2_invalid_response_has_response_data(self):
        with fudge.patched_context(DefaultResponse, 'is_valid', return_false):
            r = self.client.post(self.url, self.valid_data)
            self.assertContains(r, 'Response Data')

    def test_step2_invalid_response_shows_errors(self):
        with fudge.patched_context(DefaultResponse, 'is_valid', return_false):
            r = self.client.post(self.url, self.valid_data)
            self.invalid_response_strings(r)

    def test_step2_invalid_response_with_string_exception_shows_errors(self):
        err = "exception string not a dict"

        @proxy
        def raise_exc(obj, url):
            raise InvalidResponseError(err)

        with fudge.patched_context(DefaultBackend, 'call', raise_exc):
            r = self.client.post(self.url, self.valid_data)
            self.invalid_response_strings(r)
            self.assertContains(r, err)

    def test_step2_invalid_response_with_string_dict_shows_errors(self):
        key = "dict_key_for_error"
        err = "exception has a dict of data"

        @proxy
        def raise_exc(obj, url):
            raise InvalidResponseError(
                {key: err, 'second': 'more information'})

        with fudge.patched_context(DefaultBackend, 'call', raise_exc):
            r = self.client.post(self.url, self.valid_data)
            self.invalid_response_strings(r)
            self.assertContains(r, key)
            self.assertContains(r, err)

    def test_step2_invalid_response_is_still_saveable(self):
        with fudge.patched_context(DefaultResponse, 'is_valid', return_false):
            r = self.client.post(self.url, self.valid_data)
            self.assertContains(r, 'value="Save"')

    def test_save_requires_hash(self):
        submit, r = self._prepare_step2_data(self.add_url, self.valid_data)
        submit[r.context['hash_field']] = "invalid"
        self.client.post(self.add_url, submit)

        self.assertEqual(Embed.objects.count(), self.obj_count)

    def test_bad_security_hash_on_step2_remains_on_step2(self):
        submit, r = self._prepare_step2_data(self.url, self.valid_data)
        submit[r.context['hash_field']] = 'invalid'

        r2 = self.client.post(self.url, submit)
        self._on_step2('assertTrue', r2)

    def test_save_creates_object(self):
        submit, _ = self._prepare_step2_data(self.add_url, self.valid_data)
        r = self.client.post(self.add_url, submit)

        self.assertRedirects(r, self.changelist_url)
        self.assertEqual(Embed.objects.count(), 2)
        self.assertEqual(
            Embed.objects.get(pk=2).url,
            self.valid_data['url'])


class EmbedAdminAddTestCase(EmbedAdminBaseTestCase, TestCase):
    def setUp(self):
        super(EmbedAdminAddTestCase, self).setUp()
        self.url = self.add_url

    def test_first_submit_button_text(self):
        r = self.client.get(self.url)
        self.assertEqual(r.context['form1_submit_text'], 'Preview')

    @unittest.skipIf(django.VERSION < (1, 4), 'html feature added in Django 1.4')
    def test_first_submit_button_html(self):
        r = self.client.get(self.url)
        self.assertContains(
            r,
            '<input type="submit" class="default" value="Preview">',
            html=True)

    def test_step1_doesnt_have_response_data(self):
        r = self.client.get(self.url)
        self.assertNotContains(r, 'Response Data')

    def test_add_page_doesnt_have_delete(self):
        r = self.client.get(self.url)
        self.assertNotContains(r, 'href="delete/"')
        r = self.client.post(self.url, self.valid_data)
        self.assertNotContains(r, 'href="delete/"')

    def test_duplicate_response_flag_cannot_be_true(self):
        r = self.client.post(self.url, self.valid_data)
        self.assertFalse(r.context['duplicate_response'])

    def test_cannot_add_without_permission(self):
        add_perm = Permission.objects.get(codename="add_embed")
        chg_perm = Permission.objects.get(codename="change_embed")
        self.user.is_superuser = False
        self.user.user_permissions.add(add_perm, chg_perm)
        self.user.save()

        r = self.client.get(self.url)
        self.assertContains(r, 'Add embed')

        self.user.user_permissions.remove(add_perm)
        self.user.save()

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 403)


class EmbedAdminChangeTestCase(EmbedAdminBaseTestCase, TestCase):
    def setUp(self):
        super(EmbedAdminChangeTestCase, self).setUp()
        self.url = reverse('admin:embeds_embed_change', args=[1])
        self.current_data = dict(
            url=self.embed.url,
            backend=self.embed.backend.pk)

    def test_first_submit_button_text(self):
        r = self.client.get(self.url)
        self.assertEqual(
            r.context['form1_submit_text'],
            'Request new data & Preview')

    @unittest.skipIf(django.VERSION < (1, 4), 'html feature added in Django 1.4')
    def test_first_submit_button_html(self):
        r = self.client.get(self.url)
        self.assertContains(
            r,
            '<input type="submit" class="default" value="Request new data & Preview">',
            html=True)

    def test_step1_has_response_data(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'Response Data')

    def test_change_page_has_delete_link(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'href="delete/"')
        r = self.client.post(self.url, self.current_data)
        self.assertContains(r, 'href="delete/"')

    def test_no_delete_link_without_permission(self):
        chg_perm = Permission.objects.get(codename="change_embed")
        del_perm = Permission.objects.get(codename="delete_embed")
        self.user.is_superuser = False
        self.user.user_permissions.add(chg_perm, del_perm)
        self.user.save()

        r = self.client.get(self.url)
        self.assertContains(r, 'href="delete/"')
        self.assertTrue(r.context['has_delete_permission'])

        self.user.user_permissions.remove(del_perm)
        self.user.save()

        r = self.client.get(self.url)
        self.assertNotContains(r, 'href="delete/"')
        self.assertFalse(r.context['has_delete_permission'])

    def test_cannot_delete_without_permission(self):
        del_perm = Permission.objects.get(codename="delete_embed")
        self.user.is_superuser = False
        self.user.user_permissions.add(del_perm)
        self.user.save()

        r = self.client.get("%sdelete/" % self.url)
        self.assertEqual(r.status_code, 200)

        self.user.user_permissions.remove(del_perm)
        self.user.save()

        r = self.client.get("%sdelete/" % self.url)
        self.assertEqual(r.status_code, 403)

    def test_cannot_change_without_permission(self):
        chg_perm = Permission.objects.get(codename="change_embed")
        self.user.is_superuser = False
        self.user.user_permissions.add(chg_perm)
        self.user.save()

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

        self.user.user_permissions.remove(chg_perm)
        self.user.save()

        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 403)

    @unittest.skipIf(django.VERSION >= (1, 5), 'pre-Django 1.5 required a 404.html template')
    def test_invalid_object_id_attempts_404(self):
        from django.template import TemplateDoesNotExist
        with self.assertRaisesRegexp(TemplateDoesNotExist, '404.html'):
            self.client.get(reverse('admin:embeds_embed_change', args=[100]))

    @unittest.skipIf(django.VERSION < (1, 5), 'Django 1.5 has a default 404.html')
    def test_invalid_object_id_returns_404(self):
        r = self.client.get(reverse('admin:embeds_embed_change', args=[100]))
        self.assertEqual(r.status_code, 404)

    def test_shows_duplicate_response_message(self):
        _, r = self._prepare_step2_data(self.url, self.current_data)
        self.assertTrue(r.context['duplicate_response'])
        self.assertContains(r, 'There is no new response data')

    def test_duplicate_response_doesnt_have_save_button(self):
        _, r = self._prepare_step2_data(self.url, self.current_data)
        self.assertNotContains(r, 'value="Save"')

    def test_new_response_doesnt_have_duplicate_response_message(self):
        self.embed.response_cache = {"different": "data"}
        self.embed.save()
        _, r = self._prepare_step2_data(self.url, self.current_data)
        self.assertNotContains(r, 'There is no new response data')

    def test_new_response_can_save(self):
        self.embed.response_cache = {"different": "data"}
        self.embed.save()
        _, r = self._prepare_step2_data(self.url, self.current_data)
        self.assertContains(r, 'value="Save"')

    def test_changing_existing_data_updates_the_record(self):
        self.current_data['url'] = "http://anew.url.com/"
        submit, _ = self._prepare_step2_data(self.url, self.current_data)
        r = self.client.post(self.url, submit)

        self.assertRedirects(r, self.changelist_url)
        self.assertEqual(Embed.objects.count(), 1)
        self.assertEqual(
            Embed.objects.get(pk=1).url,
            "http://anew.url.com/")
