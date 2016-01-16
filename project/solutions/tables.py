from models import Solution

import django_tables2 as tables

from django.core.urlresolvers import reverse_lazy


class SolutionTable(tables.Table):
    class Meta:
        model = Solution
