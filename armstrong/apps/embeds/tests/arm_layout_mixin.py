import fudge
from django.db import models
from django.test import TestCase

from ..arm_layout_mixin import TemplatesByResponseTypeMixin

__all__ = ['CommonMixin', 'TemplatesByResponseTypeTestCase']


class Parent(models.Model, TemplatesByResponseTypeMixin):
    response = None
    type = None


class Child(Parent):
    pass


class CommonMixin(object):
    def setUp(self):
        self.tpl_name = "tpl"
        self.type_name = 'embed'

    def path_opts(self, obj, use_fallback=False):
        return dict(
            base=obj.base_layout_directory,
            app=obj._meta.app_label,
            model=obj._meta.module_name,
            type=self.type_name,
            tpl=obj.fallback_template_name if use_fallback else self.tpl_name)

    def compare_templates(self, obj, expected, **kwargs):
        opts = self.path_opts(obj, **kwargs)
        final = [line % opts for line in expected]
        result = obj.get_layout_template_name(self.tpl_name)
        self.assertEqual(result, final)


class TemplatesByResponseTypeTestCase(CommonMixin, TestCase):
    def test_sanity_check_mixin_has_methods(self):
        obj = TemplatesByResponseTypeMixin()
        self.assertTrue(hasattr(obj, 'get_layout_template_name'))

    def test_object_requires_type_and_typename(self):
        class Stub(models.Model, TemplatesByResponseTypeMixin):
            pass

        obj = Stub()
        obj.response = fudge.Fake().is_a_stub()
        with self.assertRaisesRegexp(AttributeError, "has no attribute 'type'"):
            obj.get_layout_template_name(self.tpl_name)

        obj.type = fudge.Fake()
        with self.assertRaises(AttributeError):
            obj.get_layout_template_name(self.tpl_name)

    def test_object_requires_response(self):
        with self.assertRaisesRegexp(AttributeError, "has no attribute 'response'"):
            TemplatesByResponseTypeMixin().get_layout_template_name(self.tpl_name)

    def test_object_response_checks_validity(self):
        obj = TemplatesByResponseTypeMixin()
        obj.response = fudge.Fake().expects('is_valid')
        obj.get_layout_template_name(self.tpl_name)

    def test_non_model_without_type_or_response_returns_empty(self):
        obj = TemplatesByResponseTypeMixin()
        obj.response = None
        obj.type = None
        self.assertEqual(obj.get_layout_template_name(self.tpl_name), [])

    def test_non_model_with_type_and_response_returns_empty(self):
        obj = TemplatesByResponseTypeMixin()
        obj.response = fudge.Fake().expects('is_valid').returns(True)
        obj.type = fudge.Fake().has_attr(name=self.type_name)
        self.assertEqual(obj.get_layout_template_name(self.tpl_name), [])

    def test_model_without_type_or_response_uses_fallback(self):
        obj = Parent()
        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_model_without_type_with_invalid_response_uses_fallback(self):
        obj = Parent()
        obj.response = fudge.Fake().expects('is_valid').returns(False)

        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_model_without_type_with_valid_response(self):
        obj = Parent()
        obj.response = fudge.Fake().expects('is_valid').returns(True)

        expected = ['%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected)

    def test_model_with_type_without_response_uses_fallback(self):
        obj = Parent()
        obj.type = fudge.Fake().has_attr(name=self.type_name)

        expected = [
            '%(base)s/%(app)s/%(model)s/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_model_with_type_and_invalid_response_uses_fallback(self):
        obj = Parent()
        obj.response = fudge.Fake().expects('is_valid').returns(False)
        obj.type = fudge.Fake().has_attr(name=self.type_name)

        expected = [
            '%(base)s/%(app)s/%(model)s/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_model_with_type_and_valid_response(self):
        obj = Parent()
        obj.response = fudge.Fake().expects('is_valid').returns(True)
        obj.type = fudge.Fake().has_attr(name=self.type_name)

        expected = [
            '%(base)s/%(app)s/%(model)s/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/%(model)s/%(tpl)s.html']
        self.compare_templates(obj, expected)

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

    def test_child_model_without_type_or_response_uses_fallback(self):
        obj = Child()
        expected = [
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_child_model_without_type_with_invalid_response_uses_fallback(self):
        obj = Child()
        obj.response = fudge.Fake().expects('is_valid').returns(False)
        expected = [
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_child_model_without_type_with_valid_response(self):
        obj = Child()
        obj.response = fudge.Fake().expects('is_valid').returns(True)
        expected = [
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected)

    def test_child_model_with_type_without_response_uses_fallback(self):
        obj = Child()
        obj.type = fudge.Fake().has_attr(name=self.type_name)
        expected = [
            '%(base)s/%(app)s/child/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_child_model_with_type_and_invalid_response_uses_fallback(self):
        obj = Child()
        obj.response = fudge.Fake().expects('is_valid').returns(False)
        obj.type = fudge.Fake().has_attr(name=self.type_name)
        expected = [
            '%(base)s/%(app)s/child/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected, use_fallback=True)

    def test_child_model_with_type_and_valid_response(self):
        obj = Child()
        obj.response = fudge.Fake().expects('is_valid').returns(True)
        obj.type = fudge.Fake().has_attr(name=self.type_name)
        expected = [
            '%(base)s/%(app)s/child/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(type)s/%(tpl)s.html',
            '%(base)s/%(app)s/child/%(tpl)s.html',
            '%(base)s/%(app)s/parent/%(tpl)s.html']
        self.compare_templates(obj, expected)
