from django.http import Http404
from django.shortcuts import render

from problems.description import IDescriptionImageLoader, render_description
from problems.models import ProblemRelatedFile
from storage.storage import create_storage
from storage.utils import serve_resource, serve_resource_metadata


class DescriptionImageLoader(IDescriptionImageLoader):
    def __init__(self, problem_id):
        self._problem_id = problem_id

    def get_image_list(self):
        return ProblemRelatedFile.objects.\
            filter(problem_id=self._problem_id).\
            filter(file_type__in=ProblemRelatedFile.TEST_CASE_IMAGE_FILE_TYPES).\
            values_list('filename', flat=True)


class TestCaseResultMixin(object):
    def serve_testcaseresult_page(self, testcaseresult, data_url_pattern, image_url_pattern, item_id, refer_to_problem):
        limit = 2**12
        max_lines = 32
        max_line_length = None
        storage = create_storage()

        context = {
            'test_case_result': testcaseresult,
            'data_url_pattern': data_url_pattern,
            'image_url_pattern': image_url_pattern,
            'item_id': item_id,
            'input_repr': storage.represent(testcaseresult.input_resource_id, limit=limit, max_lines=max_lines, max_line_length=max_line_length),
            'output_repr': storage.represent(testcaseresult.output_resource_id, limit=limit, max_lines=max_lines, max_line_length=max_line_length),
            'answer_repr': storage.represent(testcaseresult.answer_resource_id, limit=limit, max_lines=max_lines, max_line_length=max_line_length),
            'stdout_repr': storage.represent(testcaseresult.stdout_resource_id, limit=limit, max_lines=max_lines, max_line_length=max_line_length),
            'stderr_repr': storage.represent(testcaseresult.stderr_resource_id, limit=limit, max_lines=max_lines, max_line_length=max_line_length),
            'wide': not (self.request.GET.get('c') == '1'),
            'can_refer_to_problem': refer_to_problem,
        }

        test_case = testcaseresult.test_case
        if test_case is not None:

            loader = DescriptionImageLoader(test_case.problem_id)

            context['test_case'] = test_case
            context['description'] = render_description(test_case.description, loader)

        template_name = 'solutions/testcaseresult.html'
        return render(self.request, template_name, context)

    def serve_testcaseresult_data(self, mode, testcaseresult):
        resource_id = {
            'input': testcaseresult.input_resource_id,
            'output': testcaseresult.output_resource_id,
            'answer': testcaseresult.answer_resource_id,
            'stdout': testcaseresult.stdout_resource_id,
            'stderr': testcaseresult.stderr_resource_id,
        }.get(mode)

        return serve_resource(self.request, resource_id, 'text/plain')

    def serve_testcaseresult_image(self, filename, testcaseresult):
        if testcaseresult.test_case is None:
            raise Http404('Test case result is not associated with a valid test case')

        f = ProblemRelatedFile.objects.\
            filter(problem_id=testcaseresult.test_case.problem_id).\
            filter(file_type__in=ProblemRelatedFile.TEST_CASE_IMAGE_FILE_TYPES).\
            filter(filename=filename).\
            first()
        return serve_resource_metadata(self.request, f)
