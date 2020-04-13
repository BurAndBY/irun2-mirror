from django.db.models import Q, Max
from six.moves import reduce
import operator


class FolderAccessChecker(object):
    folder_model = None
    folder_access_model = None
    folder_model_object_field = None

    @classmethod
    def check(cls, user, object_id):
        '''
        returns a number:
        * 0 — no access,
        * 1 — read access,
        * 2 — write access
        '''
        clauses = []

        # Get all folders which directly contain the given object
        for tree_id, lft, rght in cls.folder_model.objects.\
                filter(**{'{}__id'.format(cls.folder_model_object_field): object_id}).\
                values_list('tree_id', 'lft', 'rght').\
                order_by():
            clauses.append(
                Q(folder__tree_id=tree_id) &
                Q(folder__lft__lte=lft) &
                Q(folder__rght__gte=rght)
            )

        if not clauses:
            return 0

        res = cls.folder_access_model.objects.filter(group__users=user).filter(reduce(operator.or_, clauses)).aggregate(Max('mode'))
        return res.get('mode__max') or 0
