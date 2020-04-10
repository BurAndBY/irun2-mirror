from django.utils.translation import ugettext_lazy as _


class AccessMode(object):
    READ = 1
    WRITE = 2

    CHOICES = (
        (READ, _('Read')),
        (WRITE, _('Write')),
    )
