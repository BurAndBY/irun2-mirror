from django.test import TestCase

from .access import Permissions


class FooPermissions(Permissions):
    READ = 1 << 0


class BarPermissions(FooPermissions):
    WRITE = 1 << 1
    EXECUTE = 1 << 2


class PermissionsTests(TestCase):
    def test_simple(self):
        f = BarPermissions(BarPermissions.READ | BarPermissions.EXECUTE)
        assert f.can_read
        assert not f.can_write
        assert f.can_execute

    def test_default(self):
        f = BarPermissions()
        assert not f.can_read
        assert not f.can_write
        assert not f.can_execute

    def test_all(self):
        f = BarPermissions.all()
        assert f.can_read
        assert f.can_write
        assert f.can_execute

    def test_ctor(self):
        BarPermissions(100500)
        with self.assertRaises(TypeError):
            BarPermissions('a')
