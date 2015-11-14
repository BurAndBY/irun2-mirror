import django_filters

from .models import Problem


class ProblemFilter(django_filters.FilterSet):
    class Meta:
        model = Problem
        fields = ['id', 'number', 'full_name', 'short_name']
