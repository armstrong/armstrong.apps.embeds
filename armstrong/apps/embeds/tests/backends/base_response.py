from django.test import TestCase as DjangoTestCase

from armstrong.apps.embeds.backends.base_response import Response
from ._common import CommonResponseTestCaseMixin


class ResponseTestCase(CommonResponseTestCaseMixin, DjangoTestCase):
    response_cls = Response

    def test_is_valid_is_not_implemented(self):
        self.assertRaises(NotImplementedError, self.response_cls().is_valid)

    def test_is_valid_is_implemented(self):
        class CustomResponse(self.response_cls):
            def is_valid(self):
                return True
        self.assertTrue(CustomResponse().is_valid())
