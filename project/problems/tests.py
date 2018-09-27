from __future__ import unicode_literals

from django.test import TestCase

from problems.description import IDescriptionImageLoader, render_description


class SimpleDescriptionImageLoader(IDescriptionImageLoader):
    def __init__(self, images):
        self._images = images

    def get_image_list(self):
        return self._images


class DescriptionTests(TestCase):
    def test_simple(self):
        loader = SimpleDescriptionImageLoader(['1.png'])
        r = render_description(
            'Look at the <image>: ${image:1.png}. Text following & the image.',
            loader
        )

        self.assertEqual(r.text, 'Look at the <image>: . Text following & the image.')
        self.assertEqual(r.images, ['1.png'])

    def test_404(self):
        loader = SimpleDescriptionImageLoader([])
        r = render_description(r'${image:404.png}', loader)
        self.assertEqual(r.text, '')
        self.assertEqual(r.images, [])
