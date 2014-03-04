import fudge

from armstrong.apps.embeds.models import Backend
from armstrong.apps.embeds.forms import EmbedForm
from .models import fake_backend_init
from ._utils import TestCase


class EmbedFormTestCase(TestCase):
    fixtures = ['embed_backends.json']

    def setUp(self):
        self.form = EmbedForm

        # Remove everything but the default Backend
        Backend.objects.exclude(slug="default").delete()

    def test_backend_can_be_empty(self):
        f = self.form(data=dict(url='www.url.com'))
        self.assertTrue(f.is_valid())

    def test_empty_backend_auto_assigns(self):
        f = self.form(data=dict(url='www.url.com'))
        f.is_valid()  # trigger cleaning
        self.assertEqual(
            f.cleaned_data['backend'],
            Backend.objects.get(slug='default'))

    def test_empty_backend_auto_assigns_higher_priority(self):
        with fudge.patched_context(Backend, '__init__', fake_backend_init):
            b1 = Backend.objects.create(name='b1', slug='b1', regex='.*', priority=5)

            f = self.form(data=dict(url='www.url.com'))
            f.is_valid()  # trigger cleaning
            self.assertEqual(f.cleaned_data['backend'], b1)

    def test_choosen_backend_doesnt_auto_assign(self):
        with fudge.patched_context(Backend, '__init__', fake_backend_init):
            Backend.objects.create(name='b1', slug='b1', regex='.*', priority=5)

            f = self.form(data=dict(url='www.url.com', backend=1))
            f.is_valid()  # trigger cleaning
            self.assertEqual(
                f.cleaned_data['backend'],
                Backend.objects.get(slug='default'))

    def test_invalid_url_causes_backend_field_to_be_excluded(self):
        """
        If the backend field isn't excluded by the form, object
        instantiation will fail because the Model attr cannot be null.

        """
        f = self.form(data=dict(url=''))
        self.assertTrue(not f._meta.exclude or 'backend' not in f._meta.exclude)
        f.full_clean()
        self.assertTrue('backend' in f._meta.exclude)

    def test_invalid_url_causes_backend_to_fail_if_not_excluded(self):
        """Use the normal ModelForm.clean()"""

        class MockForm(self.form):
            def clean(obj):
                return super(self.form, obj).clean()

        f = MockForm(data=dict(url=''))
        self.assertRaisesRegexp(
            ValueError,
            'does not allow null values',
            f.full_clean)
