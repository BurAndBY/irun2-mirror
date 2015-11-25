from django.shortcuts import render
from mptt.forms import TreeNodeChoiceField
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse

from problems.models import Problem, ProblemFolder
from django import forms


# Create your views here.
def about(request):
    return render(request, 'common/about.html', {})


def make_folder_selection_form(Object, ObjectFolder):
    class ObjectForm(forms.Form):
        folders = TreeNodeChoiceField(queryset=ObjectFolder.objects.all(),
                                      widget=forms.Select(attrs={'class': 'form-control'}))
    return ObjectForm


def choose(request):
    ProblemForm = make_folder_selection_form(Problem, ProblemFolder)
    form = ProblemForm()
    return render(request, 'common/choose.html', {'form': form})


def listf(request, folder_id):
    problems = Problem.objects.filter(folders__id=folder_id)
    data = [{'id': p.id, 'name': p.full_name} for p in problems]

    return JsonResponse({'data': data}, safe=True)
