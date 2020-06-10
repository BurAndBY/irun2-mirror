from common.tree.fields import ThreePanelModelMultipleChoiceField

from problems.loader import ProblemFolderLoader
from problems.models import Problem, ProblemFolderAccess


class ThreePanelGenericProblemMultipleChoiceField(ThreePanelModelMultipleChoiceField):
    loader_cls = ProblemFolderLoader
    folder_access_model = ProblemFolderAccess

    @classmethod
    def build_pk2folders(cls, pks):
        pk2folders = {}
        # Use LEFT OUTER JOIN to validate that problem pks are correct
        for pk, folder_id in Problem.objects.\
                filter(pk__in=pks).\
                values_list('pk', 'folders__id').\
                order_by():
            pk2folders.setdefault(pk, []).append(folder_id)

        return pk2folders

    @classmethod
    def load_folder(cls, folder_id):
        return Problem.objects.filter(folders__id=folder_id)
