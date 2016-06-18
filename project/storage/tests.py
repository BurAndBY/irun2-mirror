# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from .storage import ResourceId, FileSystemStorage, ResourseRepresentation
from .validators import validate_filename

import os
import shutil
import tempfile


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
    def _run_simple(self, fs, msg, resource_id_string):
        # msg should be plain ASCII string

        h = fs.save(ContentFile(msg))
        self.assertTrue(type(h) is ResourceId)
        self.assertEqual(str(h), resource_id_string)

        # read completely
        blob_read, is_complete = fs.read_blob(h, len(msg) * 10)
        self.assertTrue(is_complete)
        self.assertEqual(blob_read, msg)

        blob_read, is_complete = fs.read_blob(h, len(msg))
        self.assertTrue(is_complete)
        self.assertEqual(blob_read, msg)

        # read partially
        partial_length = len(msg) // 2
        if partial_length < len(msg):
            blob_read, is_complete = fs.read_blob(h, partial_length)
            self.assertFalse(is_complete)
            self.assertEqual(blob_read, msg[:partial_length])

        # represent
        representation = fs.represent(h)
        self.assertTrue(type(representation) is ResourseRepresentation)
        self.assertTrue(representation.is_complete())
        self.assertTrue(representation.is_utf8())
        self.assertEqual(representation.text, msg)

    def test_blob(self):
        dirpath = tempfile.mkdtemp()
        try:
            fs = FileSystemStorage(os.path.join(dirpath, 'filestorage'))

            msg = 'The quick brown fox jumps over the lazy dog'
            sha1 = '2fd4e1c67a2d28fced849ee1bb76e7391b93eb12'
            self._run_simple(fs, msg, sha1)

            self._run_simple(fs, '', '')
            self._run_simple(fs, '0', '30')  # ASCII '0' = 48 = 0x30
            self._run_simple(fs, '00', '3030')
            self._run_simple(fs, '0123456789', '30313233343536373839')
            self._run_simple(fs, 'hello', 'hello'.encode('hex'))

            does_not_exist = ResourceId.parse('59db6ba4a6aff5ed3d980542daf41be65624a1e8')
            self.assertTrue(fs.represent(does_not_exist) is None)

        finally:
            shutil.rmtree(dirpath)


class FilenameValidatorTests(TestCase):
    def test_good(self):
        NAMES = (
            u'a', u'123', u'sol.cpp', u'.cpp', u'statement.tex',
            u'a plus b.c', u'привет.pas', u'решение участника.exe',
            u'Разбор задачи (Пупкин В., 3 курс).doc',
            u'Главная — Insight Runner.html',
            u'あ',
            u'lpt10', u'console', u'1.aux',
            u'1. cpp', u'1 . cpp'
        )
        for name in NAMES:
            validate_filename(name)

    def _check_fail(self, *args):
        for name in args:
            with self.assertRaises(ValidationError):
                validate_filename(name)

    def test_type_mismatch(self):
        self._check_fail(None, 1, 3.14159, [], {})

    def test_empty(self):
        self._check_fail(u'')

    def test_non_printable_chars(self):
        self._check_fail(u'tab\tseparated.txt', u'\x00', u'hello\x00world.bmp', u'hello\x01world.bmp', u'\u001f.dpr')

    def test_reserved(self):
        self._check_fail(u'a/b.txt', u'a?b.txt', u'1.*', u'\\fpmi-stud\\source.cpp', u'../../etc/passwd')
        self._check_fail(u'cgi-bin?param-value')
        self._check_fail(u'BinaryTree <T extends Comparable <T>>.java')

    def test_windows(self):
        self._check_fail(u'con', u'CON', u'CoN', u'lpt9', 'aux.cpp', 'aux.1.cpp', 'prn')

    def test_end(self):
        self._check_fail(u'1.cpp.', u'1.cpp. ', u'1. .', u'.', u' ')
