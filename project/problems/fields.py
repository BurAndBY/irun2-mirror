from django.utils.translation import ugettext_lazy as _

from common.tree.fields import ThreePanelModelMultipleChoiceField

from problems.models import Problem, ProblemFolder, ProblemFolderAccess


class ThreePanelGenericProblemMultipleChoiceField(ThreePanelModelMultipleChoiceField):
    root_name = _('Problems')
    model = Problem
    folder_model = ProblemFolder
    folder_access_model = ProblemFolderAccess

    @classmethod
    def build_pk2folders(cls, pks):
        pk2folders = {}
        for pk, folder_id in Problem.folders.through.objects.\
                filter(problem_id__in=pks).\
                values_list('problem_id', 'problemfolder_id').\
                order_by():
            pk2folders.setdefault(pk, []).append(folder_id)

        # Put root folder
        for pk in pks:
            pk2folders.setdefault(pk, [None])

        return pk2folders

    @classmethod
    def load_folder(cls, folder_id):
        return Problem.objects.filter(folders__id=folder_id)
