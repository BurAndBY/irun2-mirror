from django.utils.translation import ugettext_lazy as _

from storage.storage import create_storage

from .calcpermissions import calculate_permissions
from .models import Solution


class SourceCodeToCompare(object):
    def __init__(self, solution_id, user):
        self.solution_id = solution_id

        self.solution = None
        self.permissions = None
        self.environment = None
        self.text = None
        self.error = None

        self._load(user)

        assert (self.text is not None) or (self.error is not None)

    def _load(self, user):
        self.solution = Solution.objects.filter(pk=self.solution_id).first()
        if self.solution is None:
            self.error = _('not found')
            return

        self.permissions, self.environment = calculate_permissions(self.solution, user)

        if not self.permissions.source_code:
            self.error = _('access denied')
            return

        storage = create_storage()
        source_repr = storage.represent(self.solution.source_code.resource_id)
        if source_repr is None:
            self.error = _('no data')
            return

        if source_repr.is_binary():
            self.error = _('the file is binary')
            return

        if not source_repr.is_complete():
            self.error = _('the file is too big')
            return

        self.text = source_repr.complete_text

        if self.text is None:
            self.error = _('unknown error')
            return


def fetch_solution(solution, user):
    return SourceCodeToCompare(solution, user)
