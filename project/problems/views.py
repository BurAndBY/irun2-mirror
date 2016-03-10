# -*- coding: utf-8 -*-

import json
import mimetypes
import operator
import re

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q, Count
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.utils.translation import ugettext_lazy as _

from mptt.templatetags.mptt_tags import cache_tree_children

from cauth.mixins import StaffMemberRequiredMixin
from common.folderutils import lookup_node_ex, cast_id, _fancytree_recursive_node_to_dict
from common.networkutils import redirect_with_query_string
from common.pageutils import paginate
from common.views import IRunnerBaseListView, IRunnerListView
from solutions.forms import SolutionForm
from storage.storage import create_storage
from storage.utils import serve_resource, serve_resource_metadata, store_and_fill_metadata
import solutions.utils

from .forms import ProblemForm, ProblemSearchForm, TestDescriptionForm, TestUploadOrTextForm, TestUploadForm, ProblemRelatedDataFileForm, ProblemRelatedSourceFileForm
from .forms import TeXForm, ProblemRelatedTeXFileForm
from .models import Problem, ProblemRelatedFile, TestCase, ProblemFolder
from .navigator import Navigator
from .statement import StatementRepresentation
from .texrenderer import render_tex_with_header, render_tex
from .description import IDescriptionImageLoader, render_description
from .tabs import PROBLEM_TAB_MANAGER

'''
Problem statement
'''


class ProblemStatementMixin(object):
    @staticmethod
    def _normalize(filename):
        return filename.rstrip('/')

    def is_aux_file(self, filename):
        return filename is not None and len(ProblemStatementView._normalize(filename)) > 0

    def serve_aux_file(self, request, problem_id, filename):
        filename = ProblemStatementView._normalize(filename)

        related_file = get_object_or_404(ProblemRelatedFile, problem_id=problem_id, filename=filename)
        mime_type, encoding = mimetypes.guess_type(filename)

        content_type = mime_type
        if content_type == 'text/html':
            content_type += '; charset=utf-8'

        return serve_resource(request, related_file.resource_id, content_type=content_type)

    def make_statement(self, problem):
        related_files = problem.problemrelatedfile_set.all()

        tex_statement_resource_id = None
        html_statement_name = None

        for related_file in related_files:
            ft = related_file.file_type

            if ft == ProblemRelatedFile.STATEMENT_HTML:
                if html_statement_name is None:
                    html_statement_name = related_file.filename

            elif ft == ProblemRelatedFile.STATEMENT_TEX:
                if tex_statement_resource_id is None:
                    tex_statement_resource_id = related_file.resource_id

        st = StatementRepresentation(problem)

        # TeX
        if st.is_empty and tex_statement_resource_id is not None:
            storage = create_storage()
            tex_data = storage.represent(tex_statement_resource_id)
            if tex_data is not None and tex_data.complete_text is not None:
                render_result = render_tex(tex_data.complete_text, problem.input_filename, problem.output_filename)
                st.content = render_result.output

        # HTML
        if st.is_empty and html_statement_name is not None:
            st.iframe_name = html_statement_name

        return st


'''
Alternative folder tree
'''


class FancyTreeMixin(object):
    @staticmethod
    def _list_folders():
        root_nodes = cache_tree_children(ProblemFolder.objects.all())
        dicts = []
        for n in root_nodes:
            dicts.append(_fancytree_recursive_node_to_dict(n))

        return json.dumps(dicts)

    @staticmethod
    def _list_folder_contents(folder_id):
        problems = Problem.objects.filter(folders__id=folder_id)
        result = [[str(p.id), p.full_name] for p in problems]
        return result


class ShowTreeView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request):
        tree_data = self._list_folders()
        return render(request, 'problems/tree.html', {
            'tree_data': tree_data
        })


class ShowTreeFolderView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request, folder_id):
        folder = get_object_or_404(ProblemFolder, pk=folder_id)
        tree_data = self._list_folders()
        return render(request, 'problems/tree.html', {
            'tree_data': tree_data,
            'cur_folder_id': folder.id,
            'cur_folder_name': folder.name,
            'table_data': json.dumps(self._list_folder_contents(folder_id))
        })


class ShowTreeFolderJsonView(StaffMemberRequiredMixin, FancyTreeMixin, generic.View):
    def get(self, request, folder_id):
        folder = ProblemFolder.objects.filter(pk=folder_id).first()
        name = folder.name if folder is not None else ''
        data = self._list_folder_contents(folder_id)
        return JsonResponse({'id': folder_id, 'name': name, 'data': data}, safe=True)


'''
Single problem management
'''


class BaseProblemView(StaffMemberRequiredMixin, generic.View):
    tab = None

    def _load(self, problem_id):
        return get_object_or_404(Problem, pk=problem_id)

    def _make_context(self, problem, extra=None):
        tab_manager = PROBLEM_TAB_MANAGER
        active_tab = tab_manager.get(self.tab)
        active_tab_url_pattern = active_tab.url_pattern if active_tab is not None else 'problems:overview'

        context = {
            'problem': problem,
            'active_tab': self.tab,
            'navigator': Navigator(problem.id, self.request.GET),
            'tab_manager': tab_manager,
            'active_tab_url_pattern': active_tab_url_pattern,
        }
        if extra is not None:
            context.update(extra)
        return context


'''
Overview
'''


class ProblemOverviewView(BaseProblemView):
    tab = 'overview'
    template_name = 'problems/overview.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        context = self._make_context(problem)
        context['test_count'] = problem.testcase_set.count()
        context['solution_count'] = problem.solution_set.count()
        context['file_count'] = problem.problemrelatedfile_set.count()
        return render(request, self.template_name, context)


'''
Solutions
'''


class ProblemSolutionsView(BaseProblemView, IRunnerBaseListView):
    tab = 'solutions'
    template_name = 'problems/solutions.html'
    paginate_by = 12

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        solutions = problem.solution_set.prefetch_related('compiler').select_related('source_code', 'best_judgement').order_by('-reception_time', 'id')
        self.object_list = solutions

        context = self.get_context_data(**self._make_context(problem))
        return render(request, self.template_name, context)


'''
Statement
'''


class ProblemStatementView(ProblemStatementMixin, BaseProblemView):
    tab = 'statement'
    template_name = 'problems/statement.html'

    def get(self, request, problem_id, filename):
        problem = self._load(problem_id)

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem_id, filename)

        st = self.make_statement(problem)

        context = self._make_context(problem)
        context['statement'] = st
        return render(request, self.template_name, context)


class ProblemEditView(BaseProblemView):
    tab = 'overview'
    template_name = 'problems/edit.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        form = ProblemForm(instance=problem)

        context = self._make_context(problem)
        context['form'] = form
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        form = ProblemForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('problems:overview', args=(problem.id,)))

        context = self._make_context(problem)
        context['form'] = form
        return render(request, self.template_name, context)


'''
Tests
'''


class ProblemTestsView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/tests.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        test_cases = problem.testcase_set.all()

        context = self._make_context(problem, {'test_cases': test_cases})
        return render(request, self.template_name, context)


class DescriptionImageLoader(IDescriptionImageLoader):
    def __init__(self, problem, test_number):
        self._problem = problem
        self._test_number = test_number

    def get_image_list(self):
        return self._problem.problemrelatedfile_set.\
            filter(file_type__in=ProblemRelatedFile.TEST_CASE_IMAGE_FILE_TYPES).\
            values_list('filename', flat=True)


class ProblemTestsTestView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/show_test.html'

    def get(self, request, problem_id, test_number):
        problem = self._load(problem_id)
        problem_id = int(problem_id)
        test_number = int(test_number)

        test_case = TestCase.objects.filter(problem_id=problem_id, ordinal_number=test_number).first()
        if test_case is None:
            return redirect_with_query_string(request, 'problems:tests', problem.id)

        total_tests = TestCase.objects.filter(problem_id=problem_id).count()

        storage = create_storage()
        input_repr = storage.represent(test_case.input_resource_id)
        answer_repr = storage.represent(test_case.answer_resource_id)

        loader = DescriptionImageLoader(problem, test_number)
        description = render_description(test_case.description, loader)

        context = self._make_context(problem, {
            'problem_id': problem_id,
            'current_test': test_number,
            'prev_test': test_number - 1 if test_number > 1 else total_tests,
            'next_test': test_number + 1 if test_number < total_tests else 1,
            'total_tests': total_tests,
            'input_repr': input_repr,
            'answer_repr': answer_repr,
            'description': description,
            'time_limit': test_case.time_limit,
            'memory_limit': test_case.memory_limit,
            'points': test_case.points,
        })
        return render(request, self.template_name, context)


class ProblemTestsTestImageView(BaseProblemView):
    def get(self, request, problem_id, test_number, filename):
        problem = self._load(problem_id)
        related_file = problem.problemrelatedfile_set.\
            filter(file_type__in=ProblemRelatedFile.TEST_CASE_IMAGE_FILE_TYPES).\
            filter(filename=filename).\
            first()
        return serve_resource_metadata(request, related_file)


class ProblemTestsTestDataView(BaseProblemView):
    download = False
    kind = None

    def get(self, request, problem_id, test_number):
        self._load(problem_id)
        resource_id = None
        test_case = get_object_or_404(TestCase, problem_id=problem_id, ordinal_number=test_number)

        if self.kind == 'input':
            resource_id = test_case.input_resource_id
        elif self.kind == 'answer':
            resource_id = test_case.answer_resource_id

        return serve_resource(self.request, resource_id, content_type='text/plain', force_download=self.download)


class ProblemTestsTestEditView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/edit_test.html'

    def _make_data_form(self, storage, resource_id, prefix, data=None, files=None):
        representation = storage.represent(resource_id)
        text = representation.editable_text
        if text is not None:
            return TestUploadOrTextForm(data=data, files=files, prefix=prefix, initial={'text': text})
        else:
            return TestUploadForm(data=data, files=files, prefix=prefix, representation=representation)

    def _extract_form_result(self, form):
        '''
        Returns file object if file must be replaced, else returns None (leave the initial data untouched).
        '''
        upload = form.cleaned_data['upload']
        if upload is None:
            text = form.cleaned_data.get('text')
            if text is not None:
                upload = ContentFile(text.encode('utf-8'))
        return upload

    def get(self, request, problem_id, test_number):
        problem = self._load(problem_id)
        test_case = get_object_or_404(TestCase, problem_id=problem_id, ordinal_number=test_number)

        storage = create_storage()
        input_form = self._make_data_form(storage, test_case.input_resource_id, 'input')
        answer_form = self._make_data_form(storage, test_case.answer_resource_id, 'answer')
        description_form = TestDescriptionForm(instance=test_case)

        context = self._make_context(problem, {
            'input_form': input_form,
            'answer_form': answer_form,
            'description_form': description_form,
            'test_number': test_number,
        })

        return render(request, self.template_name, context)

    field_names = {
        'points': _('score'),
        'time_limit': _('time limit'),
        'memory_limit': _('memory limit'),
        'description': _('description'),
        'input_resource_id': _('input file'),
        'answer_resource_id': _('answer file'),
    }

    def _notify_about_changes(self, test_number, changed_fields):
        message = unicode(_('Test case #%(number)s has been saved.') % {'number': test_number})

        names = []
        for field in changed_fields:
            name = self.field_names.get(field)
            if name:
                names.append(name)
        if names:
            message += u' '
            message += unicode(_('Changes:'))
            message += u' '
            message += u', '.join(unicode(name) for name in names)
            message += u'.'
        return message

    def post(self, request, problem_id, test_number):
        problem = self._load(problem_id)
        test_case = get_object_or_404(TestCase, problem_id=problem_id, ordinal_number=test_number)

        storage = create_storage()
        input_form = self._make_data_form(storage, test_case.input_resource_id, 'input', data=request.POST, files=request.FILES)
        answer_form = self._make_data_form(storage, test_case.answer_resource_id, 'answer', data=request.POST, files=request.FILES)
        description_form = TestDescriptionForm(instance=test_case, data=request.POST)

        if input_form.is_valid() and answer_form.is_valid() and description_form.is_valid():
            test_case = description_form.save(commit=False)

            changed = description_form.changed_data

            input_file = self._extract_form_result(input_form)
            if input_file is not None:
                resource_id_before = test_case.input_resource_id
                test_case.set_input(storage, input_file)
                if resource_id_before != test_case.input_resource_id:
                    changed.append('input_resource_id')

            answer_file = self._extract_form_result(answer_form)
            if answer_file is not None:
                resource_id_before = test_case.answer_resource_id
                test_case.set_answer(storage, answer_file)
                if resource_id_before != test_case.answer_resource_id:
                    changed.append('answer_resource_id')

            if changed:
                messages.add_message(request, messages.SUCCESS, self._notify_about_changes(test_number, changed))

            test_case.save()
            return redirect_with_query_string(request, 'problems:show_test', problem.id, test_number)

        context = self._make_context(problem, {
            'input_form': input_form,
            'answer_form': answer_form,
            'description_form': description_form,
            'test_number': test_number,
        })
        return render(request, self.template_name, context)


'''
Problem files
'''


class ProblemFilesView(BaseProblemView):
    tab = 'files'
    template_name = 'problems/files.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        related_files = problem.problemrelatedfile_set.all()
        related_source_files = problem.problemrelatedsourcefile_set.all().prefetch_related('compiler')

        context = self._make_context(problem, {
            'related_files': related_files,
            'related_source_files': related_source_files,
        })
        return render(request, self.template_name, context)


class ProblemFilesFileOpenView(BaseProblemView):
    download = False

    def get(self, request, problem_id, file_id, filename):
        problem = self._load(problem_id)
        related_file = get_object_or_404(problem.problemrelatedfile_set, pk=file_id, filename=filename)
        return serve_resource_metadata(request, related_file, force_download=self.download)


class ProblemFilesSourceFileOpenView(BaseProblemView):
    download = False

    def get(self, request, problem_id, file_id, filename):
        problem = self._load(problem_id)
        related_file = get_object_or_404(problem.problemrelatedsourcefile_set, pk=file_id, filename=filename)
        return serve_resource_metadata(request, related_file, content_type='text/plain', force_download=self.download)


class ProblemFilesBaseFileEditView(BaseProblemView):
    tab = 'files'
    template_name = 'problems/edit_file.html'
    form_class = None

    def get_object(self, problem, file_id):
        raise NotImplementedError()

    def get(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = self.get_object(problem, file_id)
        form = self.form_class(instance=related_file)
        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = self.get_object(problem, file_id)
        form = self.form_class(request.POST, request.FILES, instance=related_file)
        if form.is_valid():
            form.save(commit=False)
            store_and_fill_metadata(form.cleaned_data['upload'], related_file)
            related_file.save()
            return redirect('problems:files', problem.id)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)


class ProblemFilesDataFileEditView(ProblemFilesBaseFileEditView):
    form_class = ProblemRelatedDataFileForm

    def get_object(self, problem, file_id):
        return get_object_or_404(problem.problemrelatedfile_set, pk=file_id)


class ProblemFilesSourceFileEditView(ProblemFilesBaseFileEditView):
    form_class = ProblemRelatedSourceFileForm

    def get_object(self, problem, file_id):
        return get_object_or_404(problem.problemrelatedsourcefile_set, pk=file_id)


class ProblemFilesBaseFileDeleteView(BaseProblemView):
    tab = 'files'
    template_name = 'problems/delete_file.html'

    def get_queryset(self, problem, file_id):
        raise NotImplementedError()

    def get(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = self.get_queryset(problem, file_id).first()
        if related_file is None:
            return redirect('problems:files', problem.id)
        context = self._make_context(problem, {'related_file': related_file})
        return render(request, self.template_name, context)

    def post(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        self.get_queryset(problem, file_id).delete()
        return redirect('problems:files', problem.id)


class ProblemFilesDataFileDeleteView(ProblemFilesBaseFileDeleteView):
    def get_queryset(self, problem, file_id):
        return problem.problemrelatedfile_set.filter(pk=file_id)


class ProblemFilesSourceFileDeleteView(ProblemFilesBaseFileDeleteView):
    def get_queryset(self, problem, file_id):
        return problem.problemrelatedsourcefile_set.filter(pk=file_id)

'''
Submit
'''


class ProblemSubmitView(BaseProblemView):
    tab = 'submit'
    template_name = 'problems/submit.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        form = SolutionForm()
        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        form = SolutionForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                solution = solutions.utils.new_solution(
                    request,
                    form.cleaned_data['compiler'],
                    form.cleaned_data['text'],
                    form.cleaned_data['upload'],
                    problem_id=problem.id,
                )
                solutions.utils.judge(solution)

            return redirect('problems:submission', problem.id, solution.id)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)


class ProblemSubmissionView(BaseProblemView):
    tab = 'submit'
    template_name = 'problems/submission.html'

    def get(self, request, problem_id, solution_id):
        problem = self._load(problem_id)
        if problem.solution_set.filter(id=solution_id).count() == 0:
            raise Http404()

        context = self._make_context(problem, {'solution_id': solution_id})
        return render(request, self.template_name, context)


'''
All problems: folders
'''


class ProblemFolderMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ProblemFolderMixin, self).get_context_data(**kwargs)
        cached_trees = ProblemFolder.objects.all().get_cached_trees()
        node_ex = lookup_node_ex(self.kwargs['folder_id_or_root'], cached_trees)

        context['cached_trees'] = cached_trees
        context['folder_id'] = node_ex.folder_id
        context['active_tab'] = 'folders'
        return context


class ShowFolderView(StaffMemberRequiredMixin, ProblemFolderMixin, IRunnerListView):
    template_name = 'problems/list_folder.html'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super(ShowFolderView, self).get_context_data(**kwargs)
        folder_id_or_root = self.kwargs['folder_id_or_root']
        if folder_id_or_root:
            context['query_string'] = '?nav-folder={0}'.format(folder_id_or_root)
        return context

    def get_queryset(self):
        folder_id = cast_id(self.kwargs['folder_id_or_root'])
        return Problem.objects\
            .filter(folders__id=folder_id)\
            .annotate(solution_count=Count('solution'))


'''
All problems: search
'''


class SearchView(StaffMemberRequiredMixin, generic.View):
    template_name = 'problems/list_search.html'
    paginate_by = 12
    number_regex = re.compile(r'^(?P<number>\d+)(\.(?P<subnumber>\d+))?$')

    def _create_posfilter(self, word):
        m = self.number_regex.match(word)
        if m:
            posfilter = Q(number=m.group('number'))
            if m.group('subnumber') is not None:
                posfilter = posfilter & Q(subnumber=m.group('subnumber'))
        else:
            posfilter = Q(full_name__icontains=word)
        return posfilter

    def get_queryset(self, query=None):
        queryset = Problem.objects.all()
        if query is not None:
            terms = query.split()
            if terms:
                queryset = queryset.filter(reduce(operator.and_, (self._create_posfilter(term) for term in terms)))
        queryset = queryset.annotate(solution_count=Count('solution'))
        return queryset

    def get(self, request):
        form = ProblemSearchForm(request.GET)
        if form.is_valid():
            queryset = self.get_queryset(form.cleaned_data['query'])
        else:
            queryset = self.get_queryset()

        context = paginate(request, queryset, self.paginate_by)
        context['active_tab'] = 'search'
        context['form'] = form
        return render(request, self.template_name, context)


'''
TeX editor playground
'''


class TeXView(StaffMemberRequiredMixin, generic.View):
    template_name = 'problems/tex_playground.html'

    def get(self, request):
        form = TeXForm()
        context = {
            'form': form,
            'render_url': reverse('problems:tex_playground_render'),
        }
        return render(request, self.template_name, context)


def get_tex_preview(form, problem=None):
    result = {}
    if form.is_valid():
        source = form.cleaned_data['source']
        if problem is None:
            render_result = render_tex(source)
        else:
            render_result = render_tex(source, input_filename=problem.input_filename, output_filename=problem.output_filename)
        result['output'] = render_result.output
        result['log'] = render_result.log
    else:
        log_lines = []
        for field, errors in form.errors.items():
            log_lines.extend(u'— {0}'.format(e) for e in errors)
        result['log'] = '\n'.join(log_lines)
    return result


class TeXRenderView(StaffMemberRequiredMixin, generic.View):
    def post(self, request):
        form = TeXForm(request.POST)
        return JsonResponse(get_tex_preview(form))


'''
TeX editor for current problem
'''


class ProblemTeXView(BaseProblemView):
    tab = 'tex'
    template_name = 'problems/texs.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        related_files = problem.problemrelatedfile_set.filter(file_type__in=ProblemRelatedFile.TEX_FILE_TYPES)
        context = self._make_context(problem, {
            'related_files': related_files,
        })
        return render(request, self.template_name, context)


class ProblemTeXRenderView(BaseProblemView):
    def post(self, request, problem_id):
        problem = self._load(problem_id)
        form = TeXForm(request.POST)
        return JsonResponse(get_tex_preview(form, problem))


class ProblemTeXEditView(BaseProblemView):
    tab = 'tex'
    template_name = 'problems/edit_tex.html'

    def get(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = get_object_or_404(problem.problemrelatedfile_set, pk=file_id)
        context = self._make_context(problem)

        storage = create_storage()
        tex_data = storage.represent(related_file.resource_id)
        if tex_data is not None and tex_data.complete_text is not None:
            context['form'] = TeXForm(initial={'source': tex_data.complete_text})
            context['render_url'] = reverse('problems:tex_render', kwargs={'problem_id': problem_id})

        return render(request, self.template_name, context)

    def post(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = get_object_or_404(problem.problemrelatedfile_set, pk=file_id)
        form = TeXForm(request.POST)
        if form.is_valid():
            f = ContentFile(form.cleaned_data['source'].encode('utf-8'))
            store_and_fill_metadata(f, related_file)
            related_file.save()
            return redirect('problems:tex', problem_id)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)


def _new_related_file(problem, related_file, f):
    store_and_fill_metadata(f, related_file)
    related_file.problem_id = problem.id
    related_file.save()


class BaseProblemTeXNewView(BaseProblemView):
    tab = 'tex'
    template_name = 'problems/edit_tex.html'
    filename = None
    file_type = None

    def get_initial_data(self, problem):
        return u''

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        form = TeXForm(initial={'source': self.get_initial_data(problem)})

        meta_form = ProblemRelatedTeXFileForm(initial={'filename': self.filename})

        context = self._make_context(problem, {'form': form, 'meta_form': meta_form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        form = TeXForm(request.POST)

        related_file = ProblemRelatedFile(problem_id=problem_id, file_type=self.file_type)
        meta_form = ProblemRelatedTeXFileForm(request.POST, instance=related_file)

        if form.is_valid() and meta_form.is_valid():
            meta_form.save(commit=False)
            f = ContentFile(form.cleaned_data['source'].encode('utf-8'))
            store_and_fill_metadata(f, related_file)
            related_file.save()
            return redirect('problems:tex', problem_id)

        context = self._make_context(problem, {'form': form, 'meta_form': meta_form})
        return render(request, self.template_name, context)


class ProblemTeXNewStatementView(BaseProblemTeXNewView):
    filename = 'statement.tex'
    file_type = ProblemRelatedFile.STATEMENT_TEX


class ProblemTeXEditRelatedFileView(BaseProblemView):
    def get(self, request, problem_id, file_id, filename):
        problem = self._load(problem_id)
        related_file = problem.problemrelatedfile_set.filter(filename=filename).first()
        return serve_resource_metadata(request, related_file)
