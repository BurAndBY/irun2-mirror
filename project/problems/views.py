# -*- coding: utf-8 -*-

import json
import mimetypes
import operator
import re
import zipfile
import collections

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import F, Q, Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from mptt.templatetags.mptt_tags import cache_tree_children

from api.queue import ValidationInQueue, ChallengedSolutionInQueue, enqueue, bulk_enqueue
from cauth.mixins import StaffMemberRequiredMixin
from common.cast import make_int_list_quiet
from common.constants import CHANGES_HAVE_BEEN_SAVED
from common.folderutils import lookup_node_ex, cast_id, _fancytree_recursive_node_to_dict
from common.networkutils import redirect_with_query_string
from common.outcome import Outcome
from common.pageutils import paginate
from common.views import IRunnerListView
from solutions.filters import apply_state_filter, apply_compiler_filter
from solutions.forms import SolutionForm, AllSolutionsFilterForm
from solutions.models import Challenge, ChallengedSolution, Judgement
from storage.storage import create_storage
from storage.utils import serve_resource, serve_resource_metadata, store_and_fill_metadata, parse_resource_id
import solutions.utils

from .forms import ProblemForm, ProblemSearchForm, TestDescriptionForm, TestUploadOrTextForm, TestUploadForm, ProblemRelatedDataFileForm, ProblemRelatedSourceFileForm
from .forms import TeXForm, ProblemRelatedTeXFileForm, MassSetTimeLimitForm, MassSetMemoryLimitForm, ProblemFoldersForm, ProblemTestArchiveUploadForm
from .forms import ProblemRelatedDataFileNewForm, ProblemRelatedSourceFileNewForm, ValidatorForm, ChallengeForm
from .models import Problem, ProblemRelatedFile, ProblemRelatedSourceFile, TestCase, ProblemFolder, Validation
from .navigator import Navigator
from .statement import StatementRepresentation
from .texrenderer import render_tex
from .description import IDescriptionImageLoader, render_description
from .tabs import PROBLEM_TAB_MANAGER
from .validation import revalidate_testset

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
        context['folders'] = problem.folders.all()
        return render(request, self.template_name, context)


'''
Solutions
'''


class ProblemSolutionsView(BaseProblemView):
    tab = 'solutions'
    template_name = 'problems/solutions.html'
    paginate_by = 25

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        form = AllSolutionsFilterForm(request.GET)

        queryset = problem.solution_set.\
            prefetch_related('author', 'compiler').\
            select_related('source_code', 'best_judgement').\
            order_by('-reception_time', 'id')

        if form.is_valid():
            queryset = apply_state_filter(queryset, form.cleaned_data['state'])
            queryset = apply_compiler_filter(queryset, form.cleaned_data['compiler'])

        context = paginate(request, queryset, self.paginate_by)
        context = self._make_context(problem, context)
        context['form'] = form
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


'''
Tests
'''
ValidatedTestCase = collections.namedtuple('ValidatedTestCase', 'test_case is_valid validator_message')


class ProblemTestsView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/tests.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        context = {}

        validated_inputs = {}
        validation = Validation.objects.filter(problem=problem).first()
        if validation is not None:
            if validation.validator_id is not None:
                context['validation_enabled'] = True
                context['validation_general_failure_reason'] = validation.general_failure_reason

            for test_case_validation in validation.testcasevalidation_set.all():
                validated_inputs[test_case_validation.input_resource_id] = (test_case_validation.is_valid, test_case_validation.validator_message)

        validated_test_cases = []
        test_cases = problem.testcase_set.all().order_by('ordinal_number')

        stats = collections.Counter()
        all_test_count = 0

        for test_case in test_cases:
            is_valid, validator_message = validated_inputs.get(test_case.input_resource_id, (None, None))
            stats[is_valid] += 1
            all_test_count += 1
            validated_test_cases.append(ValidatedTestCase(test_case, is_valid, validator_message))

        if all_test_count > 0:
            if stats[True] == all_test_count:
                context['validation_status'] = 'GOOD'
            elif stats[False] > 0:
                context['validation_status'] = 'BAD'
            elif stats[None] > 0:
                context['validation_status'] = 'UNKNOWN'

        context['validated_test_cases'] = validated_test_cases
        context = self._make_context(problem, context)
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

            input_file = input_form.extract_file_result()
            # Returns file object if file must be replaced, else returns None (leave the initial data untouched).
            if input_file is not None:
                resource_id_before = test_case.input_resource_id
                test_case.set_input(storage, input_file)
                if resource_id_before != test_case.input_resource_id:
                    changed.append('input_resource_id')
                    revalidate_testset(problem.id)

            answer_file = answer_form.extract_file_result()
            if answer_file is not None:
                resource_id_before = test_case.answer_resource_id
                test_case.set_answer(storage, answer_file)
                if resource_id_before != test_case.answer_resource_id:
                    changed.append('answer_resource_id')

            if changed:
                messages.add_message(request, messages.INFO, self._notify_about_changes(test_number, changed))

            test_case.save()
            return redirect_with_query_string(request, 'problems:show_test', problem.id, test_number)

        context = self._make_context(problem, {
            'input_form': input_form,
            'answer_form': answer_form,
            'description_form': description_form,
            'test_number': test_number,
        })
        return render(request, self.template_name, context)


class ProblemTestsNewView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/edit_test.html'

    def _make_data_form(self, prefix, data=None, files=None):
        return TestUploadOrTextForm(data=data, files=files, prefix=prefix)

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        input_form = self._make_data_form('input')
        answer_form = self._make_data_form('answer')
        description_form = TestDescriptionForm(initial={'time_limit': 1000})

        context = self._make_context(problem, {
            'input_form': input_form,
            'answer_form': answer_form,
            'description_form': description_form,
        })
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        storage = create_storage()
        input_form = self._make_data_form('input', data=request.POST, files=request.FILES)
        answer_form = self._make_data_form('answer', data=request.POST, files=request.FILES)
        description_form = TestDescriptionForm(data=request.POST)

        if input_form.is_valid() and answer_form.is_valid() and description_form.is_valid():
            test_case = description_form.save(commit=False)
            test_case.set_input(storage, input_form.extract_file_result())
            test_case.set_answer(storage, answer_form.extract_file_result())
            test_case.problem = problem
            test_case.ordinal_number = problem.testcase_set.count() + 1  # TODO: fix possible data race
            test_case.save()
            revalidate_testset(problem.id)
            return redirect_with_query_string(request, 'problems:tests', problem.id)

        context = self._make_context(problem, {
            'input_form': input_form,
            'answer_form': answer_form,
            'description_form': description_form,
        })
        return render(request, self.template_name, context)


class ProblemTestsDeleteView(BaseProblemView):
    def post(self, request, problem_id, test_number):
        problem = self._load(problem_id)
        with transaction.atomic():
            problem.testcase_set.filter(ordinal_number=test_number).delete()
            # TODO: in Django 1.9: assert rows_deleted in (0, 1)
            problem.testcase_set.filter(ordinal_number__gt=test_number).update(ordinal_number=F('ordinal_number') - 1)
        return redirect_with_query_string(request, 'problems:tests', problem.id)


class ProblemTestsBatchSetView(BaseProblemView):
    template_name = 'problems/batch_edit_tests.html'
    tab = 'tests'
    form_class = None
    url_pattern = None

    def apply(self, queryset, valid_form):
        raise NotImplementedError()

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        ids = make_int_list_quiet(request.GET.getlist('id'))
        context = self._make_context(problem, {
            'form': self.form_class(),
            'ids': ids,
            'url_pattern': self.url_pattern,
        })
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        ids = make_int_list_quiet(request.POST.getlist('id'))
        form = self.form_class(request.POST)
        if form.is_valid():
            queryset = problem.testcase_set.filter(ordinal_number__in=ids)
            self.apply(queryset, form)
            return redirect_with_query_string(request, 'problems:tests', problem.id)

        context = self._make_context(problem, {
            'form': form,
            'ids': ids,
            'url_pattern': self.url_pattern,
        })
        return render(request, self.template_name, context)


class ProblemTestsSetTimeLimitView(ProblemTestsBatchSetView):
    form_class = MassSetTimeLimitForm
    url_pattern = 'problems:tests_mass_time_limit'

    def apply(self, queryset, valid_form):
        queryset.update(time_limit=valid_form.cleaned_data['time_limit'])


class ProblemTestsSetMemoryLimitView(ProblemTestsBatchSetView):
    form_class = MassSetMemoryLimitForm
    url_pattern = 'problems:tests_mass_memory_limit'

    def apply(self, queryset, valid_form):
        queryset.update(memory_limit=valid_form.cleaned_data['memory_limit'])


class ProblemTestsUploadArchiveView(BaseProblemView):
    template_name = 'problems/upload_archive.html'
    tab = 'tests'

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        form = ProblemTestArchiveUploadForm()
        description_form = TestDescriptionForm(initial={'time_limit': 1000})
        context = self._make_context(problem, {'form': form, 'description_form': description_form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        form = ProblemTestArchiveUploadForm(request.POST, request.FILES)
        description_form = TestDescriptionForm(request.POST)

        if form.is_valid() and description_form.is_valid():
            test_cases = []
            storage = create_storage()

            canonical_test_case = description_form.save(commit=False)

            with zipfile.ZipFile(form.cleaned_data['upload'], 'r', allowZip64=True) as myzip:
                for input_name, answer_name in form.cleaned_data['tests']:
                    test_case = TestCase(
                        problem=problem,
                        time_limit=canonical_test_case.time_limit,
                        memory_limit=canonical_test_case.memory_limit,
                        points=canonical_test_case.points,
                        description=canonical_test_case.description,
                    )
                    test_case.set_input(storage, ContentFile(myzip.read(input_name)))
                    test_case.set_answer(storage, ContentFile(myzip.read(answer_name)))
                    test_cases.append(test_case)

            with transaction.atomic():
                num_tests = problem.testcase_set.count()
                for test_case in test_cases:
                    num_tests += 1
                    test_case.ordinal_number = num_tests
                TestCase.objects.bulk_create(test_cases)

            msg = ungettext('%(count)d test was added.', '%(count)d tests were added.', len(test_cases)) % {'count': len(test_cases)}
            messages.add_message(request, messages.INFO, msg)
            revalidate_testset(problem.id)
            return redirect_with_query_string(request, 'problems:tests', problem.id)

        context = self._make_context(problem, {'form': form, 'description_form': description_form})
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
            filename = related_file.filename
            # Ignore the name of the uploaded file, use filename from form field.
            store_and_fill_metadata(form.cleaned_data['upload'], related_file)
            related_file.filename = filename
            related_file.save()

            if related_file.file_type == ProblemRelatedSourceFile.VALIDATOR:
                revalidate_testset(problem.id, clear=True)

            return redirect_with_query_string(request, 'problems:files', problem.id)

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


class ProblemFilesBaseFileNewView(BaseProblemView):
    tab = 'files'
    template_name = 'problems/edit_file.html'
    form_class = None

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        model_class = self.form_class.Meta.model
        form = self.form_class(instance=model_class(problem=problem))
        context = self._make_context(problem, {'form': form, 'propagate_filename': True})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        model_class = self.form_class.Meta.model
        form = self.form_class(request.POST, request.FILES, instance=model_class(problem=problem))
        if form.is_valid():
            related_file = form.save(commit=False)
            filename = related_file.filename
            # Ignore the name of the uploaded file, use filename from form field.
            store_and_fill_metadata(form.cleaned_data['upload'], related_file)
            related_file.filename = filename
            related_file.save()
            return redirect_with_query_string(request, 'problems:files', problem.id)

        context = self._make_context(problem, {'form': form, 'propagate_filename': True})
        return render(request, self.template_name, context)


class ProblemFilesDataFileNewView(ProblemFilesBaseFileNewView):
    form_class = ProblemRelatedDataFileNewForm


class ProblemFilesSourceFileNewView(ProblemFilesBaseFileNewView):
    form_class = ProblemRelatedSourceFileNewForm


class ProblemFilesBaseFileDeleteView(BaseProblemView):
    tab = 'files'
    template_name = 'problems/delete_file.html'

    def get_queryset(self, problem, file_id):
        raise NotImplementedError()

    def get(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = self.get_queryset(problem, file_id).first()
        if related_file is None:
            return redirect_with_query_string(request, 'problems:files', problem.id)
        context = self._make_context(problem, {'related_file': related_file})
        return render(request, self.template_name, context)

    def post(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        self.get_queryset(problem, file_id).delete()
        return redirect_with_query_string(request, 'problems:files', problem.id)


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

            return redirect_with_query_string(request, 'problems:submission', problem.id, solution.id)

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
                posfilter = posfilter | Q(id=m.group('number'))
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

    def _make_tex_context(self, problem, form):
        context = self._make_context(problem)
        context['form'] = form
        context['render_url'] = reverse('problems:tex_render', kwargs={'problem_id': problem.id})
        return context

    def get(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = get_object_or_404(problem.problemrelatedfile_set, pk=file_id)

        storage = create_storage()
        tex_data = storage.represent(related_file.resource_id)
        if tex_data is not None and tex_data.complete_text is not None:
            form = TeXForm(initial={'source': tex_data.complete_text})
            context = self._make_tex_context(problem, form)
        else:
            context = self._make_context(problem)

        return render(request, self.template_name, context)

    def post(self, request, problem_id, file_id):
        problem = self._load(problem_id)
        related_file = get_object_or_404(problem.problemrelatedfile_set, pk=file_id)
        form = TeXForm(request.POST)
        if form.is_valid():
            f = ContentFile(form.cleaned_data['source'].encode('utf-8'))
            store_and_fill_metadata(f, related_file)
            related_file.save()
            return redirect_with_query_string(request, 'problems:tex', problem_id)

        context = self._make_tex_context(problem, form)
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

    def _make_tex_context(self, problem, form, meta_form):
        context = self._make_context(problem)
        context['form'] = form
        context['meta_form'] = meta_form
        context['render_url'] = reverse('problems:tex_render', kwargs={'problem_id': problem.id})
        return context

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        form = TeXForm(initial={'source': self.get_initial_data(problem)})
        meta_form = ProblemRelatedTeXFileForm(initial={'filename': self.filename})

        context = self._make_tex_context(problem, form, meta_form)
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
            return redirect_with_query_string(request, 'problems:tex', problem_id)

        context = self._make_tex_context(problem, form, meta_form)
        return render(request, self.template_name, context)


class ProblemTeXNewStatementView(BaseProblemTeXNewView):
    filename = 'statement.tex'
    file_type = ProblemRelatedFile.STATEMENT_TEX


class ProblemTeXEditRelatedFileView(BaseProblemView):
    def get(self, request, problem_id, file_id, filename):
        problem = self._load(problem_id)
        related_file = problem.problemrelatedfile_set.filter(filename=filename).first()
        return serve_resource_metadata(request, related_file)


'''
Folders
'''


class ProblemFoldersView(BaseProblemView):
    tab = 'folders'
    template_name = 'problems/folders.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        form = ProblemFoldersForm(instance=problem)
        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        form = ProblemFoldersForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            if form.has_changed():
                messages.add_message(request, messages.INFO, CHANGES_HAVE_BEEN_SAVED)
            return redirect_with_query_string(request, 'problems:folders', problem.id)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)


'''
Properties
'''


class ProblemPropertiesView(BaseProblemView):
    tab = 'properties'
    template_name = 'problems/properties.html'

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
            if form.has_changed():
                messages.add_message(request, messages.INFO, CHANGES_HAVE_BEEN_SAVED)
            return redirect_with_query_string(request, 'problems:properties', problem.id)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)


'''
Images
'''


class ProblemPicturesView(BaseProblemView):
    tab = 'pictures'
    template_name = 'problems/pictures.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        pictures = []

        for related_file in problem.problemrelatedfile_set.all().order_by('filename'):
            mime_type, encoding = mimetypes.guess_type(related_file.filename)
            if mime_type is not None and mime_type.startswith('image/'):
                pictures.append(related_file)

        context = self._make_context(problem, {'pictures': pictures})
        return render(request, self.template_name, context)


'''
Validator
'''


class ProblemValidatorView(BaseProblemView):
    tab = 'validator'
    template_name = 'problems/validator.html'

    def _create_form(self, problem, data=None, initial=None):
        qs = problem.problemrelatedsourcefile_set.\
            filter(file_type=ProblemRelatedSourceFile.VALIDATOR)
        form = ValidatorForm(data=data, initial=initial, validators=qs)
        return form

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        initial = {}

        validation = Validation.objects.filter(problem=problem).first()
        if validation is not None:
            initial['validator'] = validation.validator

        form = self._create_form(problem, initial=initial)
        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        form = self._create_form(problem, data=request.POST)
        if form.is_valid():
            validator = form.cleaned_data['validator']
            need_validation = (validator is not None)
            upd = {
                'validator': validator,
                'is_pending': need_validation,
                'general_failure_reason': '',
            }
            with transaction.atomic():
                validation, _ = Validation.objects.update_or_create(problem=problem, defaults=upd)
                validation.testcasevalidation_set.all().delete()
                if need_validation:
                    enqueue(ValidationInQueue(validation.id))

            return redirect_with_query_string(request, 'problems:validator', problem.id)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)


'''
Challenges
'''


class ProblemChallengesView(BaseProblemView):
    tab = 'challenges'
    template_name = 'problems/challenges.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        challenges = Challenge.objects.\
            filter(problem=problem).\
            annotate(num_solutions=Count('challengedsolution')).\
            order_by('-creation_time').all()

        context = self._make_context(problem, {'object_list': challenges})
        return render(request, self.template_name, context)


class ProblemNewChallengeView(BaseProblemView):
    tab = 'challenges'
    template_name = 'problems/challenge_new.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        input_form = TestUploadOrTextForm()
        challenge_form = ChallengeForm(initial={'time_limit': 1000})
        context = self._make_context(problem, {'input_form': input_form, 'challenge_form': challenge_form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        input_form = TestUploadOrTextForm(request.POST, request.FILES)
        challenge_form = ChallengeForm(data=request.POST)

        if input_form.is_valid() and challenge_form.is_valid():
            storage = create_storage()
            resource_id = storage.save(input_form.extract_file_result())

            solution_ids = problem.solution_set.\
                filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.ACCEPTED).\
                values_list('id', flat=True)

            with transaction.atomic():
                challenge = Challenge(
                    author=request.user,
                    problem=problem,
                    time_limit=challenge_form.cleaned_data['time_limit'],
                    memory_limit=challenge_form.cleaned_data['memory_limit'],
                    input_resource_id=resource_id,
                )
                challenge.save()

                challenged_solutions = [ChallengedSolution(challenge=challenge, solution_id=solution_id) for solution_id in solution_ids]
                ChallengedSolution.objects.bulk_create(challenged_solutions)

                new_ids = ChallengedSolution.objects.filter(challenge=challenge).values_list('id', flat=True)
                bulk_enqueue((ChallengedSolutionInQueue(pk) for pk in new_ids), priority=7)

            return redirect_with_query_string(request, 'problems:challenge', problem.id, challenge.id)

        context = self._make_context(problem, {'input_form': input_form, 'challenge_form': challenge_form})
        return render(request, self.template_name, context)


ChallengeOutput = collections.namedtuple('ChallengeOutput', 'resource_id representation solutions percent')
ChallengeStats = collections.namedtuple('ChallengeStats', ['total', 'complete'])


def fetch_challenge_stats(problem_id, challenge_id):
    queryset = ChallengedSolution.objects.filter(challenge_id=challenge_id, challenge__problem_id=problem_id)
    total = queryset.count()
    complete = queryset.exclude(outcome=Outcome.NOT_AVAILABLE).count()
    return ChallengeStats(total, complete)


class ProblemChallengeView(BaseProblemView):
    tab = 'challenges'
    template_name = 'problems/challenge.html'

    max_bytes = 8192
    max_lines = 30

    def get(self, request, problem_id, challenge_id):
        problem = self._load(problem_id)

        challenge = Challenge.objects.filter(problem=problem, pk=challenge_id).first()
        if challenge is None:
            return redirect_with_query_string(request, 'problems:challenges', problem.id)

        storage = create_storage()

        input_repr = storage.represent(challenge.input_resource_id, limit=self.max_bytes, max_lines=self.max_lines)

        # output_resource_id -> [challenged_solutions]
        outputs = {}

        for cs in ChallengedSolution.objects.filter(challenge=challenge).order_by('-solution__reception_time'):
            resource_id = None
            if cs.outcome == Outcome.ACCEPTED and cs.output_resource_id is not None:
                resource_id = cs.output_resource_id
            outputs.setdefault(resource_id, []).append(cs)

        num_solutions = sum(len(x) for x in outputs.values())

        results = []
        for resource_id in sorted(outputs, key=lambda x: len(outputs[x]) if x is not None else -1, reverse=True):
            representation = storage.represent(resource_id, limit=self.max_bytes, max_lines=self.max_lines)
            solutions = outputs[resource_id]
            percent = 100 * len(solutions) // num_solutions
            results.append(ChallengeOutput(resource_id, representation, solutions, percent))

        progress_url = reverse('problems:challenge_status_json', kwargs={'problem_id': problem.id, 'challenge_id': challenge.id})
        context = self._make_context(problem, {
            'input_repr': input_repr,
            'challenge': challenge,
            'outputs': results,
            'stats': fetch_challenge_stats(problem.id, challenge.id),
            'progress_url': progress_url,
        })
        return render(request, self.template_name, context)


class ProblemChallengeJsonView(BaseProblemView):
    def get(self, request, problem_id, challenge_id):
        self._load(problem_id)
        stats = fetch_challenge_stats(problem_id, challenge_id)
        return JsonResponse({
            'total': stats.total,
            'value': stats.complete,
        })


class ProblemChallengeDataView(BaseProblemView):
    def get(self, request, problem_id, challenge_id, resource_id):
        return serve_resource(request, parse_resource_id(resource_id), 'text/plain')
