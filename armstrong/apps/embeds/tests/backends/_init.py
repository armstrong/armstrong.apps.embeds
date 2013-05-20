from django.test import TestCase as DjangoTestCase

from armstrong.apps.embeds.backends import get_backend


class GetBackendTestCase(DjangoTestCase):
    def test_load_no_backend_raises_error(self):
        with self.assertRaises(ImportError):
            get_backend('')

    def test_load_missing_backend_raises_error(self):
        with self.assertRaises(ImportError):
            get_backend('fake')
