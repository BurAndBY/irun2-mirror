from __future__ import unicode_literals

from django.utils.safestring import mark_safe

from .types import SolutionKind


class ProblemStats(object):
    def __init__(self):
        self.run_count = 0
        self.success_count = 0

    def register_solution(self, kind):
        self.run_count += 1
        if kind is SolutionKind.ACCEPTED:
            self.success_count += 1

    def as_html(self):
        # thin spaces
        return mark_safe(
            '{}\u2009/\u2009{}'.format(self.success_count, self.run_count)
        )
