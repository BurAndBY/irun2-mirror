# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import binascii
import six

from django.db import models
from django.utils.encoding import force_text

HASH_SIZE = 20


class ResourceId(object):
    def __init__(self, binary=b''):
        if not isinstance(binary, six.binary_type):
            raise TypeError('Binary string expected, {0} found'.format(type(binary)))
        if len(binary) > HASH_SIZE:
            raise ValueError('Resource id must have length not greater than {0}'.format(HASH_SIZE))
        self._binary = binary

    def get_binary(self):
        return self._binary

    def __str__(self):
        return force_text(binascii.b2a_hex(self._binary), encoding='ascii')

    @staticmethod
    def parse(s):
        return ResourceId(binascii.a2b_hex(s))

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self._binary == other._binary)

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_representation(self, obj):
        return force_text(obj)

    def __hash__(self):
        return hash(self._binary)

    def __len__(self):
        return len(self._binary)


class ResourceIdField(models.BinaryField):
    description = "Data storage resource identifier"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = HASH_SIZE
        super(ResourceIdField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ResourceIdField, self).deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value

        return ResourceId(six.binary_type(value))

    def to_python(self, value):
        if isinstance(value, ResourceId):
            return value

        if value is None:
            return value

        return ResourceId(six.binary_type(value))

    def get_prep_value(self, value):
        if isinstance(value, ResourceId):
            value = value.get_binary()

        return super(ResourceIdField, self).get_prep_value(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if isinstance(value, ResourceId):
            value = value.get_binary()

        return super(ResourceIdField, self).get_db_prep_value(value, connection, prepared)

    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return 'VARBINARY({})'.format(HASH_SIZE)
        else:
            return super().db_type(connection)


# Fake class to force migration
class ResourceIdFieldDeprecated(ResourceIdField):
    def db_type(self, connection):
        # Uses 'LONGBLOB' in MySQL by default
        return models.BinaryField.db_type(self, connection)
