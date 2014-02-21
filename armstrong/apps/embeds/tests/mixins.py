import fudge
from django.db import models
from django.test import TestCase

from ..mixins import TemplatesByEmbedTypeMixin


__all__ = ['CommonMixin', 'TemplatesByEmbedTypeTestCase']


class TypeModel(models.Model):
    slug = models.SlugField()


class Parent(models.Model, TemplatesByEmbedTypeMixin):
    response = None
    type = models.ForeignKey(TypeModel, null=True, blank=True)


class Child(Parent):
    pass


class CommonMixin(object):
    def path_opts(self, obj, use_fallback=False, use_type=False):
        return dict(
            base=obj.base_layout_directory,
            app=obj._meta.app_label,
            model=obj._meta.object_name.lower(),
            typemodel=self.type_name if use_type else "fail",
            type=self.type_slug if use_type else "fail",
            tpl=obj.fallback_template_name if use_fallback else self.tpl_name)

    def compare_templates(self, obj, expected, **kwargs):
        opts = self.path_opts(obj, **kwargs)
        final = [line % opts for line in expected]
        result = obj.get_layout_template_name(self.tpl_name)
        self.assertEqual(result, final)


class TemplatesByEmbedTypeTestCase(CommonMixin, TestCase):
    def setUp(self):
        self.tpl_name = "tpl"
        self.type_name = TypeModel()._meta.object_name.lower()
        self.type_slug = "photo"

    def test_object_requires_response(self):
        with self.assertRaisesRegexp(AttributeError, "has no attribute 'response'"):
            TemplatesByEmbedTypeMixin().get_layout_template_name(self.tpl_name)

    def test_object_response_checks_validity(self):
        obj = TemplatesByEmbedTypeMixin()
        obj.response = fudge.Fake().expects('is_valid')
        obj.get_layout_template_name(self.tpl_name)

    def test_non_model_without_response_returns_empty(self):
        obj = TemplatesByEmbedTypeMixin()
        obj.response = None
        self.assertEqual(obj.get_layout_template_name(self.tpl_name), [])

    def test_non_model_with_valid_response_returns_empty(self):
        obj = TemplatesByEmbedTypeMixin()
        obj.response = fudge.Fake().expects('is_valid').returns(True)
        obj.type = fudge.Fake()
        self.assertEqual(obj.get_layout_template_name(self.tpl_name), [])

    def test_model_without_response_uses_fallback(self):
        obj = Parent()
        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_model_with_invalid_response_uses_fallback(self):
        obj = Parent()
        obj.response = fudge.Fake().expects('is_valid').returns(False)

        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_model_with_valid_response(self):
        obj = Parent(type=TypeModel(slug=self.type_slug))
        obj.response = fudge.Fake().expects('is_valid').returns(True)

        expected = [
            '%(base)s/%(app)s/%(typemodel)s/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_type=True)

    def test_model_can_specify_templates_that_dont_fallback(self):
        obj = Parent()
        obj.templates_without_fallbacks.append(self.tpl_name)
        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected)

    def test_model_can_change_fallback_template(self):
        obj = Parent()
        obj.fallback_template_name = 'usethisone'
        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_child_model_without_response_uses_fallback(self):
        obj = Child()
        expected = [
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_child_model_with_invalid_response_uses_fallback(self):
        obj = Child()
        obj.response = fudge.Fake().expects('is_valid').returns(False)
        expected = [
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_child_model_with_valid_response(self):
        obj = Child(type=TypeModel(slug=self.type_slug))
        obj.response = fudge.Fake().expects('is_valid').returns(True)
        expected = [
            '%(base)s/%(app)s/%(typemodel)s/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected, use_type=True)
