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

    def test_basic(self):
        f = BarPermissions.basic()
        assert not f.can_read
        assert not f.can_write
        assert not f.can_execute

    def test_all(self):
        f = BarPermissions.all()
        assert f._value == 7
        assert f.can_read
        assert f.can_write
        assert f.can_execute

    def test_ctor(self):
        BarPermissions(100500)
        with self.assertRaises(TypeError):
            BarPermissions('a')

    def test_predefined(self):
        f = BarPermissions.allow_write()
        assert not f.can_read
        assert f.can_write

        f = BarPermissions.allow_read()
        assert f.can_read
        assert not f.can_write

    def test_predefined_combine(self):
        f = BarPermissions.allow_read() & BarPermissions.allow_execute()
        assert f.can_read
        assert not f.can_write
        assert f.can_execute

    def test_values(self):
        assert len(FooPermissions.items()) == 1
        assert len(BarPermissions.items()) == 3
