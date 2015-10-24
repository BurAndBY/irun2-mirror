from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.core.urlresolvers import reverse

from .models import ProgrammingLanguage


class IndexView(ListView):
    template_name = 'proglangs/index.html'
    context_object_name = 'programming_languages'

    def get_queryset(self):
        return ProgrammingLanguage.objects.all()


class CreateProgrammingLanguageView(CreateView):
    model = ProgrammingLanguage
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'family', 'description', 'legacy']

    def get_success_url(self):
        return reverse('proglangs:index')


class UpdateProgrammingLanguageView(UpdateView):
    model = ProgrammingLanguage
    template_name = 'proglangs/edit.html'
    fields = ['handle', 'family', 'description', 'legacy']

    def get_success_url(self):
        return reverse('proglangs:index')
