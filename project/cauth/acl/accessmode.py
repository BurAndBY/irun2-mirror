from django.utils.translation import ugettext_lazy as _


class AccessMode(object):
    READ = 1
    MODIFY = 2
    WRITE = 3

    CHOICES = (
        (READ, _('Read')),
        (MODIFY, _('Modify')),
        (WRITE, _('Write')),
    )

    FOLDER_CHOICES = CHOICES[:3]
    OBJECT_CHOICES = CHOICES[:2]
