from django.views.generic import ListView, CreateView, UpdateView
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from .models import Compiler


class IndexView(ListView):
    template_name = 'proglangs/index.html'
    context_object_name = 'compilers'

    def get_queryset(self):
        return Compiler.objects.all()


class CreateCompilerView(CreateView):
    model = Compiler
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'language', 'description', 'legacy']

    def get_success_url(self):
        return reverse('proglangs:index')

    def get_context_data(self, **kwargs):
        context = super(CreateCompilerView, self).get_context_data(**kwargs)
        context['page_title'] = _('New compiler')
        return context


class UpdateCompilerView(UpdateView):
    model = Compiler
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'language', 'description', 'legacy']

    def get_success_url(self):
        return reverse('proglangs:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateCompilerView, self).get_context_data(**kwargs)
        context['page_title'] = u'{0} {1} ({2})'.format(_('Compiler'), self.object.handle, self.object.description)
        return context
