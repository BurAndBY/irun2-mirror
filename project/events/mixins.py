from django.shortcuts import get_object_or_404

from .models import Event


class EventMixin(object):
    def dispatch(self, request, *args, **kwargs):
        slug = kwargs['slug']
        self.event = get_object_or_404(Event, slug=slug)
        return super(EventMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EventMixin, self).get_context_data(**kwargs)
        context['event'] = self.event
        return context
