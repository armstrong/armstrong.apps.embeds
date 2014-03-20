from armstrong.apps.embeds.backends.base_response import BaseResponse
from ._common import CommonResponseTestCaseMixin
from .._utils import TestCase


class ResponseTestCase(CommonResponseTestCaseMixin, TestCase):
    response_cls = BaseResponse

    def test_is_valid_is_not_implemented(self):
        self.assertRaises(NotImplementedError, self.response_cls().is_valid)

    def test_is_valid_is_implemented(self):
        class CustomResponse(self.response_cls):
            def is_valid(self):
                return True
        self.assertTrue(CustomResponse().is_valid())
