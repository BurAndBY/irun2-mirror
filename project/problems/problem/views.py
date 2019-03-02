# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import collections
import json
import mimetypes
import six
import zipfile

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import F, Count, ProtectedError, Case, When
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.utils import timezone
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from api.queue import ValidationInQueue, ChallengedSolutionInQueue, enqueue, bulk_enqueue, notify_enqueued
from cauth.mixins import LoginRequiredMixin
from common.access import PermissionCheckMixin
from common.cast import make_int_list_quiet
from common.constants import CHANGES_HAVE_BEEN_SAVED
from common.folderutils import ROOT
from common.networkutils import redirect_with_query_string
from common.outcome import Outcome
from common.pageutils import paginate
from solutions.filters import apply_state_filter, apply_compiler_filter
from solutions.forms import SolutionForm, AllSolutionsFilterForm
from solutions.models import Challenge, ChallengedSolution, Judgement, Rejudge
from storage.storage import create_storage
from storage.utils import serve_resource, serve_resource_metadata, store_and_fill_metadata, parse_resource_id
import solutions.utils
from solutions.utils import bulk_rejudge
from users.models import UserProfile

from problems.problem.forms import (
    ChallengeForm,
    MassSetMemoryLimitForm,
    MassSetPointsForm,
    MassSetTimeLimitForm,
    ProblemExtraInfoForm,
    ProblemFoldersForm,
    ProblemForm,
    ProblemRelatedDataFileForm,
    ProblemRelatedDataFileNewForm,
    ProblemRelatedSourceFileForm,
    ProblemRelatedSourceFileNewForm,
    ProblemRelatedTeXFileForm,
    ProblemTestArchiveUploadForm,
    ShareProblemForm,
    TestDescriptionForm,
    TestUploadForm,
    TestUploadOrTextForm,
    ValidatorForm,
)
from problems.problem.permissions import SingleProblemPermissions
from problems.problem.utils import register_new_test
from problems.problem.tabs import PROBLEM_TABS, TabManager
from problems.problem.validation import revalidate_testset

from problems.description import IDescriptionImageLoader, render_description
from problems.forms import (
    SimpleProblemForm,
    TeXForm,
)
from problems.models import (
    AccessMode,
    Problem,
    ProblemAccess,
    ProblemRelatedFile,
    ProblemRelatedSourceFile,
    TestCase,
    Validation
)
from problems.navigator import Navigator
from problems.views import get_tex_preview
from problems.views import ProblemStatementMixin


def make_initial_limits(problem):
    return {
        'time_limit': problem.get_default_time_limit(),
        'memory_limit': problem.get_default_memory_limit()
    }


'''
Single problem management
'''


class SingleProblemPermissionCheckMixin(PermissionCheckMixin):
    def _make_permissions(self, user):
        SPP = SingleProblemPermissions

        if user.is_staff:
            return SPP(SPP.ALL)
        if user.userprofile.has_access_to_problems:
            problem_id = self.kwargs['problem_id']
            access = ProblemAccess.objects.filter(problem_id=problem_id, user=user).first()
            if access is not None:
                if access.mode == AccessMode.READ:
                    return SPP()
                elif access.mode == AccessMode.WRITE:
                    return SPP(SPP.EDIT | SPP.CHALLENGE)


class BaseProblemView(LoginRequiredMixin, SingleProblemPermissionCheckMixin, generic.View):
    tab = None

    def _load(self, problem_id):
        return get_object_or_404(Problem.objects.select_related('extra'), pk=problem_id)

    def _make_context(self, problem, extra=None):
        tab_manager = TabManager(PROBLEM_TABS, self.permissions)
        active_tab = tab_manager.get(self.tab)
        active_tab_url_pattern = active_tab.url_pattern if active_tab is not None else 'problems:overview'

        context = {
            'problem': problem,
            'active_tab': self.tab,
            'navigator': Navigator(problem.id, self.request.user, self.request.GET),
            'tab_manager': tab_manager,
            'active_tab_url_pattern': active_tab_url_pattern,
            'permissions': self.permissions,
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


class ProblemSolutionsProcessView(BaseProblemView):
    def _pack_zip(self, problem, solution_ids):
        max_size = 1 * 1024 * 1024

        solutions = problem.solution_set.\
            filter(pk__in=solution_ids).\
            select_related('source_code')

        # Open StringIO to grab in-memory ZIP contents
        s = six.StringIO()

        storage = create_storage()

        # The zip compressor
        with zipfile.ZipFile(s, 'w') as zf:
            for solution in solutions:
                blob, is_complete = storage.read_blob(solution.source_code.resource_id, max_size=max_size)
                if is_complete:
                    fn = '{0}/{1}'.format(solution.id, solution.source_code.filename)
                    zf.writestr(fn, blob)

        # Grab ZIP file from in-memory, make response with correct MIME-type
        response = HttpResponse(s.getvalue(), content_type='application/x-zip-compressed')
        response['Content-Disposition'] = 'attachment; filename="solutions-{0}.zip"'.format(problem.id)
        return response

    def _rejudge(self, problem, solutions):
        with transaction.atomic():
            rejudge = bulk_rejudge(solutions, self.request.user)
        notify_enqueued()
        return redirect('solutions:rejudge', rejudge.id)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        solution_ids = make_int_list_quiet(request.POST.getlist('id'))
        if 'pack' in request.POST:
            return self._pack_zip(problem, solution_ids)

        if self.permissions.can_rejudge:
            if 'rejudge' in request.POST:
                return self._rejudge(problem, problem.solution_set.filter(pk__in=solution_ids))

            if 'rejudge_all' in request.POST:
                return self._rejudge(problem, problem.solution_set)

            if 'rejudge_accepted' in request.POST:
                return self._rejudge(problem, problem.solution_set.filter(best_judgement__status=Judgement.DONE, best_judgement__outcome=Outcome.ACCEPTED))

        return redirect_with_query_string(request, 'problems:solutions', problem.id)

'''
Statement
'''


class ProblemStatementView(ProblemStatementMixin, BaseProblemView):
    tab = 'statement'
    template_name = 'problems/statement.html'
    template_name_print = 'problems/statement_print.html'

    def get(self, request, problem_id, filename):
        problem = self._load(problem_id)

        if self.is_aux_file(filename):
            return self.serve_aux_file(request, problem_id, filename)

        st = self.make_statement(problem)

        context = self._make_context(problem)
        context['statement'] = st
        template_name = self.template_name_print if (request.GET.get('print') == '1') else self.template_name
        return render(request, template_name, context)


'''
Tests
'''
ValidatedTestCase = collections.namedtuple('ValidatedTestCase', 'test_case is_valid validator_message has_default_limits is_sample')


class ProblemTestsView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/tests.html'

    def _fill_summary(self, context, test_cases):
        total_input_size = 0
        total_answer_size = 0
        total_points = 0

        for test_case in test_cases:
            total_input_size += test_case.input_size
            total_answer_size += test_case.answer_size
            total_points += test_case.points

        context['total_input_size'] = total_input_size
        context['total_answer_size'] = total_answer_size
        context['total_points'] = total_points

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

        extra = problem.get_extra()
        sample_test_count = extra.sample_test_count if (extra is not None) else 0

        for test_case in test_cases:
            is_valid, validator_message = validated_inputs.get(test_case.input_resource_id, (None, None))
            stats[is_valid] += 1
            all_test_count += 1
            has_default_limits = (
                test_case.time_limit == problem.get_default_time_limit() and
                test_case.memory_limit == problem.get_default_memory_limit()
            )
            is_sample = (test_case.ordinal_number <= sample_test_count)
            validated_test_cases.append(ValidatedTestCase(test_case, is_valid, validator_message, has_default_limits, is_sample))

        if all_test_count > 0:
            if stats[True] == all_test_count:
                context['validation_status'] = 'GOOD'
            elif stats[False] > 0:
                context['validation_status'] = 'BAD'
            elif stats[None] > 0:
                context['validation_status'] = 'UNKNOWN'

        context['validated_test_cases'] = validated_test_cases
        self._fill_summary(context, test_cases)
        context = self._make_context(problem, context)
        return render(request, self.template_name, context)


FetchedTestCase = collections.namedtuple('FetchedTestCase', 'test_case input_repr answer_repr')


class ProblemBrowseTestsView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/tests_browse.html'
    max_lines = 10
    max_line_length = 48

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        fetched_test_cases = []
        test_cases = problem.testcase_set.all().order_by('ordinal_number')
        storage = create_storage()

        for test_case in test_cases:
            input_repr = storage.represent(test_case.input_resource_id, max_lines=self.max_lines, max_line_length=self.max_line_length)
            answer_repr = storage.represent(test_case.answer_resource_id, max_lines=self.max_lines, max_line_length=self.max_line_length)
            fetched_test_cases.append(FetchedTestCase(test_case, input_repr, answer_repr))

        context = self._make_context(problem, {'fetched_test_cases': fetched_test_cases})
        return render(request, self.template_name, context)


class ProblemReorderTestsView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/tests_reorder.html'
    requirements = SingleProblemPermissions.EDIT

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        tests_json = []
        for test_case in problem.testcase_set.all().order_by('ordinal_number'):
            tests_json.append({
                'id': test_case.id,
                'number': test_case.ordinal_number,
            })

        context = self._make_context(problem, {'tests_json': json.dumps(tests_json)})
        return render(request, self.template_name, context)

    @staticmethod
    def _parse_new_numbering(json_str):
        test_id_to_number = {}
        data = json.loads(json_str)
        number = 0
        for test in data:
            test_id = int(test['id'])
            number += 1
            test_id_to_number[test_id] = number
        return test_id_to_number

    @staticmethod
    def _fetch_old_numbering(problem_id):
        test_id_to_number = {}
        for test_id, number in TestCase.objects.filter(problem_id=problem_id).values_list('id', 'ordinal_number'):
            test_id_to_number[test_id] = number
        return test_id_to_number

    def _reorder(self, problem_id, new_numbering):
        old_numbering = self._fetch_old_numbering(problem_id)
        if old_numbering == new_numbering:  # no changes
            return False
        if sorted(old_numbering.keys()) != sorted(new_numbering.keys()):
            return False
        if sorted(old_numbering.values()) != sorted(new_numbering.values()):
            return False

        # Prevent unique constraint violation with two-step update.
        # TODO: More efficient way? Drop constraint?
        offset = len(old_numbering)
        stmt1 = []
        stmt2 = []
        for test_id, new_number in new_numbering.items():
            if old_numbering[test_id] != new_number:
                stmt1.append(When(pk=test_id, then=new_number + offset))
                stmt2.append(When(pk=test_id, then=new_number))

        with transaction.atomic():
            TestCase.objects.filter(problem_id=problem_id).update(ordinal_number=Case(*stmt1, default=F('ordinal_number')))
            TestCase.objects.filter(problem_id=problem_id).update(ordinal_number=Case(*stmt2, default=F('ordinal_number')))
        return True

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        new_numbering = None
        try:
            new_numbering = self._parse_new_numbering(request.POST.get('tests'))
        except:
            pass
            # TODO: better error handling
        if new_numbering is not None:
            if self._reorder(problem.id, new_numbering):
                messages.add_message(request, messages.INFO, _('Tests have been reordered.'))

        return redirect_with_query_string(request, 'problems:tests', problem.id)


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
            'author': test_case.author,
            'creation_time': test_case.creation_time,
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
    requirements = SingleProblemPermissions.EDIT

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
        'points': _('points'),
        'time_limit': _('time limit'),
        'memory_limit': _('memory limit'),
        'description': _('description'),
        'input_resource_id': _('input file'),
        'answer_resource_id': _('answer file'),
    }

    def _notify_about_changes(self, test_number, changed_fields):
        message = force_text(_('Test %(number)s has been saved.') % {'number': test_number})

        names = []
        for field in changed_fields:
            name = self.field_names.get(field)
            if name:
                names.append(name)
        if names:
            message += ' '
            message += force_text(_('Changes:'))
            message += ' '
            message += ', '.join(force_text(name) for name in names)
            message += '.'
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
    requirements = SingleProblemPermissions.EDIT

    def _make_data_form(self, prefix, data=None, files=None):
        return TestUploadOrTextForm(data=data, files=files, prefix=prefix)

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        input_form = self._make_data_form('input')
        answer_form = self._make_data_form('answer')
        description_form = TestDescriptionForm(initial=make_initial_limits(problem))

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
            register_new_test(test_case, problem, request)
            return redirect_with_query_string(request, 'problems:tests', problem.id)

        context = self._make_context(problem, {
            'input_form': input_form,
            'answer_form': answer_form,
            'description_form': description_form,
        })
        return render(request, self.template_name, context)


class ProblemTestsDeleteView(BaseProblemView):
    requirements = SingleProblemPermissions.EDIT

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
    requirements = SingleProblemPermissions.EDIT

    def apply(self, problem, queryset, valid_form):
        raise NotImplementedError()

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        ids = make_int_list_quiet(request.GET.getlist('id'))
        context = {
            'ids': ids,
            'url_pattern': self.url_pattern,
        }
        if self.form_class is not None:
            context['form'] = self.form_class(initial=make_initial_limits(problem))
        context = self._make_context(problem, context)
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        ids = make_int_list_quiet(request.POST.getlist('id'))

        form = None
        if self.form_class is not None:
            form = self.form_class(request.POST, initial=make_initial_limits(problem))
            ok = False
            if form.is_valid():
                ok = True
        else:
            ok = True

        if ok:
            queryset = problem.testcase_set.filter(ordinal_number__in=ids)
            self.apply(problem, queryset, form)
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

    def apply(self, problem, queryset, valid_form):
        queryset.update(time_limit=valid_form.cleaned_data['time_limit'])


class ProblemTestsSetMemoryLimitView(ProblemTestsBatchSetView):
    form_class = MassSetMemoryLimitForm
    url_pattern = 'problems:tests_mass_memory_limit'

    def apply(self, problem, queryset, valid_form):
        queryset.update(memory_limit=valid_form.cleaned_data['memory_limit'])


class ProblemTestsSetPointsView(ProblemTestsBatchSetView):
    form_class = MassSetPointsForm
    url_pattern = 'problems:tests_mass_points'

    def apply(self, problem, queryset, valid_form):
        queryset.update(points=valid_form.cleaned_data['points'])


class ProblemTestsBatchDeleteView(ProblemTestsBatchSetView):
    form_class = None
    url_pattern = 'problems:tests_mass_delete'
    template_name = 'problems/batch_delete_tests.html'
    requirements = SingleProblemPermissions.EDIT

    def apply(self, problem, queryset, valid_form):
        with transaction.atomic():
            queryset.delete()
            test_ids = problem.testcase_set.all().order_by('ordinal_number').values_list('id', flat=True)
            no = 0
            for test_id in test_ids:
                no += 1
                TestCase.objects.filter(pk=test_id, problem=problem).update(ordinal_number=no)


class ProblemTestsUploadArchiveView(BaseProblemView):
    template_name = 'problems/upload_archive.html'
    tab = 'tests'
    requirements = SingleProblemPermissions.EDIT

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        form = ProblemTestArchiveUploadForm()
        description_form = TestDescriptionForm(initial=make_initial_limits(problem))
        context = self._make_context(problem, {'form': form, 'description_form': description_form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        form = ProblemTestArchiveUploadForm(request.POST, request.FILES)
        description_form = TestDescriptionForm(request.POST)

        if form.is_valid() and description_form.is_valid():
            test_cases = []
            storage = create_storage()

            ts = timezone.now()
            canonical_test_case = description_form.save(commit=False)

            with zipfile.ZipFile(form.cleaned_data['upload'], 'r', allowZip64=True) as myzip:
                for input_name, answer_name in form.cleaned_data['tests']:
                    test_case = TestCase(
                        problem=problem,
                        time_limit=canonical_test_case.time_limit,
                        memory_limit=canonical_test_case.memory_limit,
                        points=canonical_test_case.points,
                        description=canonical_test_case.description,
                        creation_time=ts,
                        author=request.user,
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

            msg = ungettext('%(count)d test has been added.', '%(count)d tests have been added.', len(test_cases)) % {'count': len(test_cases)}
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
    requirements = SingleProblemPermissions.EDIT

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
    requirements = SingleProblemPermissions.EDIT

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
    requirements = SingleProblemPermissions.EDIT

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
                solution = solutions.utils.new_solution(request, form, problem_id=problem.id)
                solutions.utils.judge(solution)
            notify_enqueued()
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
    requirements_to_post = SingleProblemPermissions.EDIT

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
    requirements = SingleProblemPermissions.EDIT

    def get_initial_data(self, problem):
        return ''

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
    file_type = ProblemRelatedFile.STATEMENT_TEX_TEX2HTML


class ProblemTeXEditorRelatedFileView(BaseProblemView):
    def get(self, request, problem_id, filename):
        problem = self._load(problem_id)
        related_file = problem.problemrelatedfile_set.filter(filename=filename).first()
        return serve_resource_metadata(request, related_file)


'''
Folders
'''


class ProblemFoldersView(BaseProblemView):
    tab = 'folders'
    template_name = 'problems/folders.html'
    requirements = SingleProblemPermissions.MOVE

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
    requirements = SingleProblemPermissions.EDIT

    def _make_forms(self, problem, data=None):
        form = ProblemForm(data=data, instance=problem)
        initial = {'default_time_limit': problem.get_default_time_limit(), 'default_memory_limit': problem.get_default_memory_limit()}
        extra = problem.get_extra()
        extra_form = ProblemExtraInfoForm(data=data, instance=extra, initial=initial)
        return form, extra_form

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        context = self._make_context(problem)

        form, extra_form = self._make_forms(problem)
        context['form'] = form
        context['extra_form'] = extra_form
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        form, extra_form = self._make_forms(problem, request.POST)
        if form.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                form.save()
                extra = extra_form.save(commit=False)
                extra.pk = problem.id
                extra.save()

            if form.has_changed() or extra_form.has_changed():
                messages.add_message(request, messages.INFO, CHANGES_HAVE_BEEN_SAVED)
            return redirect_with_query_string(request, 'problems:properties', problem.id)

        context = self._make_context(problem)
        context['form'] = form
        context['extra_form'] = extra_form
        return render(request, self.template_name, context)


'''
Name
'''


class ProblemNameView(BaseProblemView):
    tab = 'name'
    template_name = 'problems/name.html'
    requirements = SingleProblemPermissions.EDIT

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        form = SimpleProblemForm(instance=problem)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        form = SimpleProblemForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            if form.has_changed():
                messages.add_message(request, messages.INFO, CHANGES_HAVE_BEEN_SAVED)
            return redirect_with_query_string(request, 'problems:name', problem.id)

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
    requirements = SingleProblemPermissions.EDIT

    def _create_form(self, problem, data=None, initial=None):
        qs = problem.problemrelatedsourcefile_set.\
            filter(file_type=ProblemRelatedSourceFile.VALIDATOR)
        form = ValidatorForm(data=data, initial=initial, validators=qs)
        return form

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        initial = {}
        context = {}

        validation = Validation.objects.filter(problem=problem).first()
        if validation is not None:
            initial['validator'] = validation.validator

            if validation.validator is not None:
                storage = create_storage()
                context['compiler'] = validation.validator.compiler
                context['source_repr'] = storage.represent(validation.validator.resource_id)

        form = self._create_form(problem, initial=initial)
        context['form'] = form
        context = self._make_context(problem, context)
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
            enqueued = False
            with transaction.atomic():
                validation, _ = Validation.objects.update_or_create(problem=problem, defaults=upd)
                validation.testcasevalidation_set.all().delete()
                if need_validation:
                    enqueue(ValidationInQueue(validation.id))
                    enqueued = True
            if enqueued:
                notify_enqueued()
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
    requirements = SingleProblemPermissions.CHALLENGE

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        input_form = TestUploadOrTextForm()
        challenge_form = ChallengeForm(initial=make_initial_limits(problem))
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

            enqueued = False
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
                enqueued = bulk_enqueue((ChallengedSolutionInQueue(pk) for pk in new_ids), priority=7)

            if enqueued:
                notify_enqueued()

            return redirect_with_query_string(request, 'problems:challenge', problem.id, challenge.id)

        context = self._make_context(problem, {'input_form': input_form, 'challenge_form': challenge_form})
        return render(request, self.template_name, context)


ChallengeOutput = collections.namedtuple('ChallengeOutput', 'resource_id representation solutions percent filename')
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
        resource_ids = sorted(outputs, key=lambda x: len(outputs[x]) if x is not None else -1, reverse=True)
        for i, resource_id in enumerate(resource_ids):
            representation = storage.represent(resource_id, limit=self.max_bytes, max_lines=self.max_lines)
            solutions = outputs[resource_id]
            percent = 100 * len(solutions) // num_solutions
            filename = 'challenge-{0}-output-{1:02}'.format(challenge.id, i + 1)
            results.append(ChallengeOutput(resource_id, representation, solutions, percent, filename))

        progress_url = reverse('problems:challenge_status_json', kwargs={'problem_id': problem.id, 'challenge_id': challenge.id})
        context = self._make_context(problem, {
            'input_repr': input_repr,
            'input_filename': 'challenge-{0}-input'.format(challenge.id),
            'challenge': challenge,
            'outputs': results,
            'stats': fetch_challenge_stats(problem.id, challenge.id),
            'progress_url': progress_url,
        })
        return render(request, self.template_name, context)


class ProblemChallengeAddTestView(BaseProblemView):
    requirements = SingleProblemPermissions.EDIT

    def post(self, request, problem_id, challenge_id):
        problem = self._load(problem_id)

        challenge = Challenge.objects.filter(problem=problem, pk=challenge_id).first()
        if challenge is None:
            return redirect_with_query_string(request, 'problems:challenges', problem.id)

        # throws 404 on invalid data
        answer_resource_id = parse_resource_id(request.POST.get('answer'))
        storage = create_storage()
        answer_repr = storage.represent(answer_resource_id)

        if answer_repr is not None:
            input_resource_id = challenge.input_resource_id
            input_repr = storage.represent(input_resource_id)

            if input_repr is not None:
                tc = TestCase()
                tc.input_resource_id = input_resource_id
                tc.input_size = input_repr.size
                tc.answer_resource_id = answer_resource_id
                tc.answer_size = answer_repr.size
                tc.time_limit = challenge.time_limit
                tc.memory_limit = challenge.memory_limit
                register_new_test(tc, problem, request)

        return redirect_with_query_string(request, 'problems:tests', problem.id)


class ProblemChallengeJsonView(BaseProblemView):
    def get(self, request, problem_id, challenge_id):
        self._load(problem_id)
        stats = fetch_challenge_stats(problem_id, challenge_id)
        return JsonResponse({
            'total': stats.total,
            'value': stats.complete,
        })


class ProblemChallengeDataView(BaseProblemView):
    download = False

    def _is_resource_available(self, challenge, resource_id):
        if challenge.input_resource_id == resource_id:
            return True
        if ChallengedSolution.objects.filter(challenge=challenge, output_resource_id=resource_id).exists():
            return True
        return False

    def get(self, request, problem_id, challenge_id, resource_id, filename):
        problem = self._load(problem_id)
        challenge = get_object_or_404(problem.challenge_set, pk=challenge_id)
        resource_id = parse_resource_id(resource_id)

        if self._is_resource_available(challenge, resource_id):
            return serve_resource(request, resource_id, 'text/plain', force_download=self.download)
        else:
            raise Http404('no resource found for current challenge')


'''
Delete problem
'''


class ProblemDeleteView(BaseProblemView):
    tab = 'name'
    template_name = 'problems/delete.html'
    requirements = SingleProblemPermissions.DELETE

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        context = self._make_context(problem)
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)

        deleted = False
        try:
            problem.delete()
            deleted = True
        except ProtectedError:
            pass

        if deleted:
            return redirect('problems:show_folder', ROOT)
        else:
            context = self._make_context(problem, {'error': True})
            return render(request, self.template_name, context)


'''
Rejudges
'''


class ProblemRejudgesView(BaseProblemView):
    tab = 'rejudges'
    template_name = 'problems/rejudges.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        rejudges = Rejudge.objects.\
            filter(judgement__solution__problem=problem).\
            annotate(num_solutions=Count('judgement')).\
            order_by('-creation_time', '-id').\
            distinct()

        context = self._make_context(problem, {'object_list': rejudges})
        return render(request, self.template_name, context)


'''
Access
'''


class ProblemAccessView(BaseProblemView):
    tab = 'access'
    template_name = 'problems/access.html'
    requirements_to_post = SingleProblemPermissions.EDIT

    def _load_access_control_list(self, problem):
        return ProblemAccess.objects.filter(problem=problem).order_by('id').all()

    def get(self, request, problem_id):
        problem = self._load(problem_id)
        share_form = ShareProblemForm()
        context = self._make_context(problem, {
            'share_form': share_form,
            'acl': self._load_access_control_list(problem)
        })
        return render(request, self.template_name, context)

    def post(self, request, problem_id):
        problem = self._load(problem_id)
        share_form = ShareProblemForm()
        success = False

        if 'grant' in request.POST:
            share_form = ShareProblemForm(request.POST)

            if share_form.is_valid():
                user_id = share_form.cleaned_data['user']
                ProblemAccess.objects.update_or_create(
                    problem_id=problem.id,
                    user_id=user_id,
                    defaults={
                        'mode': share_form.cleaned_data['mode'],
                        'who_granted': self.request.user,
                    }
                )
                UserProfile.objects.filter(pk=user_id).update(has_access_to_problems=True)
                success = True

        elif 'revoke' in request.POST:
            access_ids = make_int_list_quiet(request.POST.getlist('id'))
            ProblemAccess.objects.filter(problem=problem).filter(pk__in=access_ids).delete()
            success = True

        if success:
            return redirect_with_query_string(request, 'problems:access', problem.id)

        context = self._make_context(problem, {
            'share_form': share_form,
            'acl': self._load_access_control_list(problem)
        })
        return render(request, self.template_name, context)
