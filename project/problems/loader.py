from django.utils.translation import ugettext_lazy as _

from common.tree.loader import FolderLoader

from problems.models import Problem, ProblemFolder, ProblemFolderAccess


class ProblemFolderLoader(FolderLoader):
    root_name = _('Problems')
    model = Problem
    folder_model = ProblemFolder
    folder_access_model = ProblemFolderAccess

    @classmethod
    def get_extra_objects(cls, user):
        return Problem.objects.filter(problemaccess__user=user)

    @classmethod
    def get_extra_folders(cls, user):
        return ProblemFolder.objects.filter(problem__problemaccess__user=user)

    @classmethod
    def get_folder_content(cls, user, node):
        qs = Problem.objects.filter(folders__id=node.id)
        if node.access == 0:
            # partial access
            qs = qs.filter(problemaccess__user=user)
        return qs
