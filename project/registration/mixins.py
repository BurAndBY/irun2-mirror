from django.shortcuts import get_object_or_404
from django.http import Http404

from .models import IcpcCoach

import shortuuid


def _parse_uuid(s):
    try:
        return shortuuid.decode(s)
    except ValueError:
        raise Http404('invalid id: {}'.format(repr(s)))


class CoachMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.coach_id_str = kwargs['coach_id']
        coach_id = _parse_uuid(self.coach_id_str)
        self.coach = get_object_or_404(IcpcCoach, id=coach_id)
        return super(CoachMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CoachMixin, self).get_context_data(**kwargs)
        context['coach'] = self.coach
        context['coach_id_str'] = self.coach_id_str
        return context
