from django.test import TestCase
from django.core.files.base import ContentFile

from .storage import ResourceId, FileSystemStorage

import tempfile
import shutil


class DataIdTests(TestCase):
    def test_to_string(self):
        h = ResourceId('\0')
        self.assertEqual(str(h), '00')

    def test_from_string(self):
        h = ResourceId.parse('ff')
        self.assertEqual(len(h.get_binary()), 1)
        self.assertEqual(h.get_binary(), '\xff')

        with self.assertRaises(TypeError):
            ResourceId.parse('a')

        with self.assertRaises(TypeError):
            ResourceId.parse('ax')


class FileSystemStorageTests(TestCase):
    def test_blob(self):
        dirpath = tempfile.mkdtemp()
        try:
            fs = FileSystemStorage(dirpath)

            msg = 'The quick brown fox jumps over the lazy dog'
            sha1 = '2fd4e1c67a2d28fced849ee1bb76e7391b93eb12'
            h = fs.save(ContentFile(msg))
            self.assertEqual(str(h), sha1)

            h = fs.save(ContentFile(''))
            self.assertEqual(str(h), '')

            h = fs.save(ContentFile('hello'))
            self.assertEqual(str(h), 'hello'.encode('hex'))

        finally:
            shutil.rmtree(dirpath)
