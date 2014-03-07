from django.db import models

from armstrong.apps.embeds.fields import EmbedURLField
from .support.models import CustomFieldModel
from ._utils import TestCase


class CustomFieldTestCase(TestCase):
    """
    Test SetResponseFieldMixin and ResetResponseMixin

    Only testing one of our two fields because they both use the same mixin
    and descriptor mixin. Also, EmbedModelTestCase tests both fields anyway
    except for raising the TypeError.

    """
    def test_field_requires_response_attr_kwarg(self):
        with self.assertRaisesRegexp(TypeError, 'requires a "response_attr"'):
            class Model(models.Model):
                broken = EmbedURLField()

    def test_initially_setting_field_doesnt_delete_response(self):
        model = CustomFieldModel()
        model.field = "newurl.com"
        self.assertEqual(model.response, 'testing')

    def test_changing_field_deletes_response(self):
        model = CustomFieldModel(field="url.com")
        model.field = "newurl.com"
        with self.assertRaises(AttributeError):
            model.response

    def test_changing_an_empty_field_doesnt_delete_response(self):
        model = CustomFieldModel(field="")
        model.field = "newurl.com"
        self.assertEqual(model.response, 'testing')

    def test_setting_same_field_value_doesnt_delete_response(self):
        model = CustomFieldModel(field="url.com")
        model.field = "url.com"
        self.assertEqual(model.response, 'testing')
