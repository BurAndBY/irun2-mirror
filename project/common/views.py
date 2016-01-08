from django.shortcuts import render
from mptt.forms import TreeNodeChoiceField
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from problems.models import Problem, ProblemFolder
from django import forms
from django.http import Http404
from django.core.paginator import Paginator
from collections import namedtuple
from django.contrib import auth

import django.views.generic.list


def home(request):
    return render(request, 'common/home.html', {})


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
    #problems = Problem.objects.filter(folders__id=folder_id)
    problems = auth.get_user_model().objects.filter(userprofile__folder_id=folder_id)
    #data = [{'id': p.id, 'name': p.full_name} for p in problems]
    data = [{'id': p.id, 'name': p.get_full_name()} for p in problems]

    return JsonResponse({'data': data}, safe=True)


class IRunnerPaginationContext(object):
    def __init__(self):
        self.page_obj = None
        self.object_count = 0
        self.per_page_count = 0
        self.query_param_size = ''
        self.query_params_other = ''
        self.page_size_constants = []


class IRunnerBaseListView(django.views.generic.list.BaseListView):
    page_size_constants = [7, 12, 25, 50, 100]
    size_kwarg = 'size'

    def _parse_size_param(self):
        '''
        Parses size param from query string.
        '''
        size = self.request.GET.get(self.size_kwarg)
        if size is None:
            return None  # param was not passed

        try:
            size = int(size)
        except (TypeError, ValueError):
            raise Http404('That page size is not an integer')
        if size < 0:
            raise Http404('That page size is less than zero')
        return size

    def get_paginate_by(self, queryset):
        '''
        Paginate by specified value in querystring, or use default class property value.
        '''
        size = self._parse_size_param()
        if size is not None:
            return None if size == 0 else size
        else:
            return self.paginate_by

    def _list_page_sizes(self, size):
        '''
        Prepares ordered list of integers.
        '''
        s = set(self.page_size_constants)
        s.add(size)
        s.add(self.paginate_by)
        return sorted(filter(None, s))

    def _get_size_query_param(self):
        '''
        Returns '' or '&size=N' string.
        '''
        result = ''
        size = self._parse_size_param()
        if size is not None:
            # safe: no need to urlencode integers
            result = '&{0}={1}'.format(self.size_kwarg, size)
        return result

    def _get_other_query_params(self):
        '''
        Returns '' or '&key1=value1&key2=value2...' string made up with
        params that are not related to pagination.
        '''
        params = self.request.GET.copy()
        if self.size_kwarg in params:
            params.pop(self.size_kwarg)
        if self.page_kwarg in params:
            params.pop(self.page_kwarg)

        result = params.urlencode()
        if result:
            result = '&' + result
        return result

    def _get_object_count(self, context):
        '''
        Always returns integer.
        '''
        paginator = context.get('paginator')
        if paginator is None:
            queryset = context['object_list']
            # create fake paginator to get total object list
            paginator = Paginator(queryset, 1)
        return paginator.count

    def _get_per_page_count(self, context):
        '''
        Always returns integer.
        '''
        paginator = context.get('paginator')
        if paginator is None:
            return 0
        else:
            return paginator.per_page

    def get_context_data(self, **kwargs):
        context = super(IRunnerBaseListView, self).get_context_data(**kwargs)

        pc = IRunnerPaginationContext()

        pc.page_obj = context.get('page_obj')

        pc.object_count = self._get_object_count(context)
        pc.per_page_count = self._get_per_page_count(context)

        pc.query_param_size = self._get_size_query_param()
        pc.query_params_other = self._get_other_query_params()

        pc.page_size_constants = self._list_page_sizes(pc.per_page_count)

        context['pagination_context'] = pc
        return context


class IRunnerListView(django.views.generic.list.MultipleObjectTemplateResponseMixin, IRunnerBaseListView):
    pass


def error403(request):
    return render(request, 'common/error403.html', {})


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
