import fudge
from django.core.exceptions import ImproperlyConfigured

from armstrong.apps.embeds.backends.embedly import EmbedlyResponse, EmbedlyBackend
from ._common import CommonBackendTestCaseMixin, CommonResponseTestCaseMixin
from .._utils import TestCase


class EmbedlyResponseTestCase(CommonResponseTestCaseMixin, TestCase):
    response_cls = EmbedlyResponse
    invalid_data = [
        None,
        dict(error=True),
        dict(error=404),
        dict(type='error')
    ]

    def test_get_by_type_without_a_type(self):
        response = self.response_cls()
        self.assertEqual(response._get_by_type(dict(a='key')), '')

    def test_get_by_type_when_type_isnt_in_dict(self):
        response = self.response_cls({'type': 'TestType'})
        self.assertEqual(response._get_by_type(dict(a='key')), '')

    def test_get_by_type_with_type_but_no_data(self):
        response = self.response_cls({'type': 'TestType'})
        self.assertEqual(response._get_by_type(dict(testtype='key')), '')

    def test_get_by_type_with_type_and_data(self):
        response = self.response_cls({'type': 'TestType', 'key': 'value'})
        self.assertEqual(response._get_by_type(dict(testtype='key')), 'value')

    def test_get_image_url(self):
        response = self.response_cls({'type': 'photo'})
        self.assertEqual(response.image_url, '')
        response = self.response_cls({'type': 'photo', 'url': 'works'})
        self.assertEqual(response.image_url, 'works')
        response = self.response_cls({'type': 'link', 'thumbnail_url': 'works'})
        self.assertEqual(response.image_url, 'works')
        response = self.response_cls({'type': 'video', 'thumbnail_url': 'works'})
        self.assertEqual(response.image_url, 'works')

    def test_get_image_height(self):
        response = self.response_cls({'type': 'link'})
        self.assertEqual(response.image_height, '')
        response = self.response_cls({'type': 'photo', 'height': 'works'})
        self.assertEqual(response.image_height, 'works')
        response = self.response_cls({'type': 'link', 'thumbnail_height': 'works'})
        self.assertEqual(response.image_height, 'works')
        response = self.response_cls({'type': 'video', 'thumbnail_height': 'works'})
        self.assertEqual(response.image_height, 'works')

    def test_get_image_width(self):
        response = self.response_cls({'type': 'video'})
        self.assertEqual(response.image_width, '')
        response = self.response_cls({'type': 'photo', 'width': 'works'})
        self.assertEqual(response.image_width, 'works')
        response = self.response_cls({'type': 'link', 'thumbnail_width': 'works'})
        self.assertEqual(response.image_width, 'works')
        response = self.response_cls({'type': 'video', 'thumbnail_width': 'works'})
        self.assertEqual(response.image_width, 'works')


class EmbedlyBackendTestCase(CommonBackendTestCaseMixin, TestCase):
    backend_cls = EmbedlyBackend
    response_cls = EmbedlyResponse
    bad_url = "http://iam.not.a.real.url/embed?id=123"
    url = "https://secure.flickr.com/photos/nationalgalleries/3110936222/"
    data = dict(
        original_url=url,
        type="link",
        title="Melrose Abbey",
        provider_name="Flickr",
        description="Roger Fenton 1856 Accession no. PGP 233.2 Medium Salt print from a collodion negative Size 34.00 x 42.80 cm Credit Presented anonymously through the good offices of Christie's 1998 For more information please select here.",
        thumbnail_url="https://farm4.staticflickr.com/3126/3110936222_7374acb6a6_z.jpg?zz=1",
        thumbnail_height=431,
        thumbnail_width=500)

    @fudge.patch('armstrong.apps.embeds.backends.embedly.settings')
    def test_requires_api_key_in_settings(self, fake_settings):
        with self.assertRaises(ImproperlyConfigured):
            self.backend_cls()

    def test_missing_api_key(self):
        with self.settings(EMBEDLY_KEY=None):
            with self.assertRaises(ValueError):
                self.backend_cls().call(self.url)

    def test_empty_api_key(self):
        with self.settings(EMBEDLY_KEY=''):
            with self.assertRaises(ValueError):
                self.backend_cls().call(self.url)

    def test_invalid_api_key(self):
        with self.settings(EMBEDLY_KEY='invalid_test_key'):
            response = self.backend_cls().call(self.url)
            self.assertFalse(response.is_valid())

    def test_api_server_error_is_wrapped(self):
        from armstrong.apps.embeds.backends import InvalidResponseError

        def throw_error(*args, **kwargs):
            from httplib2 import ServerNotFoundError
            raise ServerNotFoundError

        with fudge.patched_context(self.backend.client, 'oembed', throw_error):
            with self.assertRaises(InvalidResponseError):
                self.backend.call(self.url)

    def test_flickr_response(self):
        self._test_response_data(self.url, self.data)
        self._test_garbage_data_should_not_match_a_valid_response(self.url, self.data)

    def test_youtube_response(self):
        url = "https://www.youtube.com/watch?v=341Z3YW3mO0"
        data = dict(
            provider_name="YouTube",
            provider_url="http://www.youtube.com/",
            type="video",
            title="The I Files - Investigate Your World",
            author_name="The I Files",
            author_url="http://www.youtube.com/user/theifilestv",
            html='<iframe class="embedly-embed" src="//cdn.embedly.com/widgets/media.html?src=http%3A%2F%2Fwww.youtube.com%2Fembed%2F341Z3YW3mO0%3Ffeature%3Doembed&url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D341Z3YW3mO0&image=http%3A%2F%2Fi1.ytimg.com%2Fvi%2F341Z3YW3mO0%2Fhqdefault.jpg&key=internal&type=text%2Fhtml&schema=youtube" width="854" height="480" scrolling="no" frameborder="0" allowfullscreen></iframe>')

        self._test_response_data(url, data)
        self._test_garbage_data_should_not_match_a_valid_response(url, data)

    def test_vimeo_response(self):
        url = "http://vimeo.com/18150336"
        data = dict(
            provider_name="Vimeo",
            provider_url="http://www.vimeo.com/",
            type="video",
            title="Wingsuit Basejumping - The Need 4 Speed: The Art of Flight",
            author_name="Phoenix Fly",
            author_url="http://vimeo.com/phoenixfly",
            html='<iframe class="embedly-embed" src="//cdn.embedly.com/widgets/media.html?src=http%3A%2F%2Fplayer.vimeo.com%2Fvideo%2F18150336&src_secure=1&url=http%3A%2F%2Fvimeo.com%2F18150336&image=http%3A%2F%2Fi.vimeocdn.com%2Fvideo%2F117311910_1280.jpg&key=internal&type=text%2Fhtml&schema=vimeo" width="1280" height="720" scrolling="no" frameborder="0" allowfullscreen></iframe>')

        self._test_response_data(url, data)
        self._test_garbage_data_should_not_match_a_valid_response(url, data)
