from django.db.models import Q, Max
from six.moves import reduce
from collections import namedtuple
import operator

SimpleFolder = namedtuple('SimpleFolder', ['tree_id', 'lft', 'rght', 'mode'])


class FolderAccessChecker(object):
    '''
    Check result is a number:
    * 0 — no access,
    * 1 — read access,
    * 2 — write access
    '''
    folder_model = None
    folder_access_model = None
    folder_model_object_field = None

    @classmethod
    def check(cls, user, object_id):
        clauses = []

        # Get all folders which directly contain the given object
        for tree_id, lft, rght in cls.folder_model.objects.\
                filter(**{cls.folder_model_object_field: object_id}).\
                values_list('tree_id', 'lft', 'rght').\
                order_by():
            # for the given folder, the clause describes all its parent folders
            clauses.append(
                Q(folder__tree_id=tree_id) &
                Q(folder__lft__lte=lft) &
                Q(folder__rght__gte=rght)
            )

        if not clauses:
            return 0

        # Get all folder access records that belong to our user's admin groups
        # and to folders that contain the folders listed above
        # TODO: this query generates three JOIN's, but two JOIN's are enough
        res = cls.folder_access_model.objects.\
            filter(group__users=user).\
            filter(reduce(operator.or_, clauses)).\
            aggregate(Max('mode'))
        return res.get('mode__max') or 0

    @classmethod
    def bulk_check(cls, user, object_ids):
        object_ids = set(object_ids)

        # Get folders we have directly have access to
        my_folders = []
        for values in cls.folder_access_model.objects.\
                filter(group__users=user).\
                values_list('folder__tree_id', 'folder__lft', 'folder__rght', 'mode').\
                order_by():
            my_folders.append(SimpleFolder(*values))

        result = {object_id: 0 for object_id in object_ids}

        # Get folders that objecs directly belong to
        for tree_id, lft, rght, pk in cls.folder_model.objects.\
                filter(**{'{}__in'.format(cls.folder_model_object_field): object_ids}).\
                values_list('tree_id', 'lft', 'rght', cls.folder_model_object_field).\
                order_by():
            for folder in my_folders:
                if folder.tree_id == tree_id and folder.lft <= lft and rght <= folder.rght:
                    result[pk] = max(result[pk], folder.mode)

        # Verify that results are same
        # result_brute = {object_id: cls.check(user, object_id) for object_id in object_ids}
        # assert result_brute == result
        return result
