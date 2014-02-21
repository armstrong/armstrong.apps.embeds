import sys
import fudge
from StringIO import StringIO
from logging import StreamHandler
from django.template import TemplateSyntaxError
from django.test import TestCase

from ... import logger
from ...templatetags.embed_helpers import resize_iframe


__all__ = ['ResizeIframeWithoutLXMLTestCase', 'ResizeIframeTestCase']


class ResizeIframeWithoutLXMLTestCase(TestCase):
    def setUp(self):
        """
        Force import of the module we need to fake so we know the real module,
        can replace it and then restore it when the tests are finished.

        """
        import lxml.html
        self.original_module = sys.modules.get('lxml.html')
        sys.modules['lxml.html'] = fudge.Fake('lxml.html')

    def tearDown(self):
        sys.modules['lxml.html'] = self.original_module

    def test_tag_logs_error(self):
        log_capture = StringIO()
        log_handler = StreamHandler(log_capture)
        logger.addHandler(log_handler)

        resize_iframe('value', 200)
        self.assertTrue("lxml package is missing" in log_capture.getvalue())

        logger.removeHandler(log_handler)

    def test_tag_returns_untouched_value(self):
        value = 'template with a bunch of code'
        self.assertEqual(value, resize_iframe(value, 200))


class ResizeIframeTestCase(TestCase):
    def setUp(self):
        self.height = 300
        self.width = 560
        self.new_width = self.width - 1
        self.new_height = self.height - 1

    @property
    def original(self):
        return ''.join([
            '<iframe width="%s" height="%s" ' % (self.width, self.height),
            'src="http://www.youtube.com/embed/M7lc1UVf-VE" ',
            'frameborder="0" allowfullscreen></iframe>'])

    @property
    def expected_result(self):
        mod = self.original.replace(str(self.width), str(self.new_width))
        return mod.replace(str(self.height), str(self.new_height))

    def test_empty_value_returns_empty_value(self):
        self.assertEqual(resize_iframe('', 1), '')

    def test_doesnt_modify_non_iframe_dimensions(self):
        html = '<div height="100" width="200"><span height="50" width="100">Test</span></div>'
        result = resize_iframe(html, 50)
        self.assertEqual(result, html)

    def test_doesnt_modify_larger_width(self):
        result = resize_iframe(self.original, self.width + 1)
        self.assertEqual(result, self.original)

    def test_doesnt_modify_same_width(self):
        result = resize_iframe(self.original, self.width)
        self.assertEqual(result, self.original)

    def test_modifies_smaller_width(self):
        result = resize_iframe(self.original, self.new_width)
        self.assertNotEqual(result, self.original)
        self.assertEqual(self.expected_result, result)

    def test_do_nothing_if_no_width_attr(self):
        mod = self.original.replace('width', 'new')
        result = resize_iframe(mod, self.new_width)
        self.assertEqual(result, mod)

    def test_do_nothing_if_width_isnt_a_number(self):
        self.width = 'NaN'
        result = resize_iframe(self.original, self.new_width)
        self.assertEqual(result, self.original)

    def test_modifies_width_but_doesnt_require_height_attr(self):
        mod = self.original.replace('height', 'new')
        expected_result = mod.replace(str(self.width), str(self.new_width))

        result = resize_iframe(mod, self.new_width)
        self.assertNotEqual(result, mod)
        self.assertEqual(result, expected_result)

    def test_modifies_width_but_skips_height_if_not_a_number(self):
        self.height = self.new_height = "NaN"
        result = resize_iframe(self.original, self.new_width)
        self.assertNotEqual(result, self.original)
        self.assertEqual(result, self.expected_result)

    def test_scales_height_properly_in_half(self):
        self.new_width = self.width / 2
        self.new_height = self.height / 2
        result = resize_iframe(self.original, self.new_width)

        self.assertNotEqual(result, self.original)
        self.assertEqual(result, self.expected_result)

    def test_scales_height_properly_to_zero(self):
        self.new_width = 0
        self.new_height = 0
        result = resize_iframe(self.original, 0)

        self.assertNotEqual(result, self.original)
        self.assertEqual(result, self.expected_result)

    def test_raises_exception_on_negative(self):
        with self.assertRaises(TemplateSyntaxError):
            resize_iframe(self.original, -1)

    def test_handles_non_root_element_iframe(self):
        mod = ''.join(['<div><p><section>', self.original, '</section></p></div>'])
        expected_result = ''.join(['<div><p><section>', self.expected_result, '</section></p></div>'])

        result = resize_iframe(mod, self.new_width)
        self.assertNotEqual(result, mod)
        self.assertEqual(result, expected_result)

    def test_handles_multiple_iframes(self):
        mod = ''.join([self.original for i in range(0, 3)])
        result = resize_iframe(mod, self.new_width)
        self.assertNotEqual(result, mod)
        self.assertEqual(result.count(self.expected_result), 3)
