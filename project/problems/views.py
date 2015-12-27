from django.shortcuts import render

from django.shortcuts import get_object_or_404, render, render_to_response
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.urlresolvers import reverse
from django.views import generic
from django.views.generic import View
from django.shortcuts import redirect
from storage.storage import create_storage
from django.http import StreamingHttpResponse
from django.utils.translation import ugettext as _
from django.db import transaction

import json
from mptt.templatetags.mptt_tags import cache_tree_children


from .models import Problem, ProblemRelatedFile, TestCase, ProblemFolder
from .forms import ProblemForm
from solutions.forms import SolutionForm

from .filters import ProblemFilter
import mimetypes

from .texrenderer import TeXRenderer

from .statement import StatementRepresentation
import storage.utils as fsutils
from common.views import IRunnerBaseListView
import solutions.utils


# Create your views here.
class IndexView(generic.ListView):
    template_name = 'problems/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Problem.objects.all()


def problem_list(request):
    f = ProblemFilter(request.GET, queryset=Problem.objects.all())
    return render_to_response('problems/index.html', {'filter': f})


class ProblemFormNewView(View):
    template_name = 'problems/edit.html'

    def get(self, request, *args, **kwargs):
        form = ProblemForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = ProblemForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('problems:index'))

        return render(request, self.template_name, {'form': form})


class ProblemStatementMixin(object):
    @staticmethod
    def _normalize(filename):
        return filename.rstrip('/')

    def is_aux_file(self, filename):
        return filename is not None and len(ProblemStatementView._normalize(filename)) > 0

    def serve_aux_file(self, request, problem_id, filename):
        filename = ProblemStatementView._normalize(filename)

        related_file = get_object_or_404(ProblemRelatedFile, problem_id=problem_id, name=filename)
        mime_type, encoding = mimetypes.guess_type(filename)
        return fsutils.serve_resource(request, related_file.resource_id, content_type=mime_type)

    def make_statement(self, problem):
        related_files = problem.problemrelatedfile_set.all()

        tex_statement_resource_id = None
        html_statement_name = None

        for related_file in related_files:
            ft = related_file.file_type

            if ft == ProblemRelatedFile.STATEMENT_HTML:
                if html_statement_name is None:
                    html_statement_name = related_file.name

            elif ft == ProblemRelatedFile.STATEMENT_TEX:
                if tex_statement_resource_id is None:
                    tex_statement_resource_id = related_file.resource_id

        st = StatementRepresentation()

        # TeX
        if st.is_empty and tex_statement_resource_id is not None:
            storage = create_storage()
            tex_data = storage.represent(tex_statement_resource_id)
            if tex_data is not None and tex_data.complete_text is not None:
                renderer = TeXRenderer.create(problem, tex_data.complete_text)
                st.content = renderer.render_inner_html()

        # HTML
        if st.is_empty and html_statement_name is not None:
            st.iframe_name = html_statement_name

        return st


def show_test(request, problem_id, test_number):
    problem_id = int(problem_id)
    test_number = int(test_number)

    storage = create_storage()
    test_case = get_object_or_404(TestCase, problem_id=problem_id, ordinal_number=test_number)
    total_tests = TestCase.objects.filter(problem_id=problem_id).count()

    input_repr = storage.represent(test_case.input_resource_id)
    answer_repr = storage.represent(test_case.answer_resource_id)

    return render(request, 'problems/show_test.html', {
        'problem_id': problem_id,
        'current_test': test_number,
        'prev_test': test_number - 1 if test_number > 1 else total_tests,
        'next_test': test_number + 1 if test_number < total_tests else 1,
        'total_tests': total_tests,
        'input_repr': input_repr,
        'answer_repr': answer_repr,
        'description': test_case.description,
    })


def recursive_node_to_dict(node):
    result = {
        'key': node.pk,
        'title': node.name,
        'folder': True,
    }
    children = [recursive_node_to_dict(c) for c in node.get_children()]
    if children:
        result['children'] = children
    return result


def _list_folders():
    root_nodes = cache_tree_children(ProblemFolder.objects.all())
    dicts = []
    for n in root_nodes:
        dicts.append(recursive_node_to_dict(n))

    return json.dumps(dicts)


def _list_folder_contents(folder_id):
    #lb = int(folder_id) * 1000
    #ub = (int(folder_id) + 1) * 1000
    #problems = Problem.objects.filter(id__gte=lb, id__lt=ub)
    problems = Problem.objects.filter(folders__id=folder_id)
    result = [[str(p.id), p.full_name] for p in problems]
    return result


def show_tree(request):
    tree_data = _list_folders()
    return render(request, 'problems/tree.html', {
        'tree_data': tree_data
    })


def show_folder(request, folder_id):
    folder = get_object_or_404(ProblemFolder, pk=folder_id)
    tree_data = _list_folders()
    return render(request, 'problems/tree.html', {
        'tree_data': tree_data,
        'cur_folder_id': folder.id,
        'cur_folder_name': folder.name,
        'table_data': json.dumps(_list_folder_contents(folder_id))
    })


def show_folder_json(request, folder_id):
    folder = ProblemFolder.objects.filter(pk=folder_id).first()
    name = folder.name if folder is not None else ''
    data = _list_folder_contents(folder_id)
    return JsonResponse({'id': folder_id, 'name': name, 'data': data}, safe=True)


class BaseProblemView(generic.View):
    tab = None

    def _load(self, problem_id):
        return get_object_or_404(Problem, pk=problem_id)

    def _make_context(self, problem, extra=None):
        context = {
            'problem': problem,
            'active_tab': self.tab,
        }
        if extra is not None:
            context.update(extra)
        return context


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


class ProblemTestsView(BaseProblemView):
    tab = 'tests'
    template_name = 'problems/tests.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        test_cases = problem.testcase_set.all()

        context = self._make_context(problem, {'test_cases': test_cases})
        return render(request, self.template_name, context)


class ProblemFilesView(BaseProblemView):
    tab = 'files'
    template_name = 'problems/files.html'

    def get(self, request, problem_id):
        problem = self._load(problem_id)

        related_files = problem.problemrelatedfile_set.all()

        context = self._make_context(problem, {'related_files': related_files})
        return render(request, self.template_name, context)


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
                    form.cleaned_data['compiler'],
                    form.cleaned_data['text'],
                    form.cleaned_data['upload'],
                    problem=problem
                )
                solutions.utils.judge(solution)

            return redirect('problems:solutions', problem.id)

        context = self._make_context(problem, {'form': form})
        return render(request, self.template_name, context)
