from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.core.urlresolvers import reverse

from .models import Compiler


class IndexView(ListView):
    template_name = 'proglangs/index.html'
    context_object_name = 'programming_languages'

    def get_queryset(self):
        return Compiler.objects.all()


class CreateCompilerView(CreateView):
    model = Compiler
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'language', 'description', 'legacy']

    def get_success_url(self):
        return reverse('proglangs:index')


class UpdateCompilerView(UpdateView):
    model = Compiler
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'language', 'description', 'legacy']

    def get_success_url(self):
        return reverse('proglangs:index')
