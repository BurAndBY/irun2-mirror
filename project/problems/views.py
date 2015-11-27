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

import json
from mptt.templatetags.mptt_tags import cache_tree_children


from .models import Problem, ProblemRelatedFile, TestCase, ProblemFolder
from .forms import ProblemForm
from .filters import ProblemFilter
import mimetypes

from .texrenderer import TeXRenderer

from .statement import StatementRepresentation


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


class ProblemFormEditView(View):
    def get(self, request, problem_id):
        problem = get_object_or_404(Problem, pk=problem_id)
        form = ProblemForm(instance=problem)
        return render(request, 'problems/edit.html', {'form': form})

    def post(self, request, problem_id):
        problem = get_object_or_404(Problem, pk=problem_id)
        form = ProblemForm(request.POST, instance=problem)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('problems:index'))

        return render(request, 'problems/edit.html', {'form': form})


def overview(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    related_files = problem.problemrelatedfile_set.all()
    test_cases = problem.testcase_set.all()

    return render(request, 'problems/overview.html', {
        'problem': problem,
        'related_files': related_files,
        'test_cases': test_cases
    })


def tests(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    return render(request, 'problems/tests.html', {'problem': problem})


def add_test(request, problem_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    return render(request, 'problems/test.html', {'problem': problem})


class ProblemStatementView(generic.View):
    @staticmethod
    def _normalize(filename):
        return filename.rstrip('/')

    def is_aux_file(self, filename):
        return filename is not None and len(ProblemStatementView._normalize(filename)) > 0

    def serve_aux_file(self, problem_id, filename):
        filename = ProblemStatementView._normalize(filename)

        related_file = get_object_or_404(ProblemRelatedFile, problem_id=problem_id, name=filename)
        storage = create_storage()

        mime_type, encoding = mimetypes.guess_type(filename)
        data = storage.serve(related_file.resource_id)

        response = StreamingHttpResponse(data.generator, content_type=mime_type)
        response['Content-Length'] = data.size
        return response

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

    def get(self, request, problem_id, filename):
        if self.is_aux_file(filename):
            return self.serve_aux_file(problem_id, filename)

        problem = get_object_or_404(Problem, pk=problem_id)

        st = self.make_statement(problem)
        return render(request, 'problems/statement.html', {'statement': st})


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
