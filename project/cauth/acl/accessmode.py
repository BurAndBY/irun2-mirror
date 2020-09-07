from django.utils.translation import ugettext_lazy as _


class AccessMode(object):
    READ = 1
    MODIFY = 2

    CHOICES = (
        (READ, _('Read')),
        (MODIFY, _('Modify')),
    )
