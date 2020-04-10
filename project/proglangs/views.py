from __future__ import unicode_literals

from django.db import transaction
from django.views import generic
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from cauth.mixins import StaffMemberRequiredMixin

from .forms import DeleteCompilerForm
from .models import Compiler
from .usage import replace_compiler


class IndexView(StaffMemberRequiredMixin, generic.ListView):
    template_name = 'proglangs/index.html'
    context_object_name = 'compilers'

    def get_queryset(self):
        return Compiler.objects.all()


class CreateCompilerView(StaffMemberRequiredMixin, generic.CreateView):
    model = Compiler
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'language', 'description', 'default_for_courses', 'default_for_contests']

    def get_success_url(self):
        return reverse('proglangs:index')


class UpdateCompilerView(StaffMemberRequiredMixin, generic.UpdateView):
    model = Compiler
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'language', 'description', 'default_for_courses', 'default_for_contests']

    def get_success_url(self):
        return reverse('proglangs:index')


class DeleteCompilerView(StaffMemberRequiredMixin, generic.detail.TemplateResponseMixin, generic.detail.ContextMixin, generic.View):
    template_name = 'proglangs/delete.html'

    def get(self, request, pk):
        compiler = get_object_or_404(Compiler, pk=pk)
        form = DeleteCompilerForm(current_compiler=compiler)
        context = self.get_context_data(object=compiler, form=form)
        return self.render_to_response(context)

    def post(self, request, pk):
        compiler = get_object_or_404(Compiler, pk=pk)
        form = DeleteCompilerForm(request.POST, current_compiler=compiler)
        if form.is_valid():
            with transaction.atomic():
                replace_compiler(compiler.id, form.cleaned_data['replacement'].id)
                compiler.delete()
            return redirect('proglangs:index')
        context = self.get_context_data(object=compiler, form=form)
        return self.render_to_response(context)
