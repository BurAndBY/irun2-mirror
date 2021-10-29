from django.http import JsonResponse
from django.utils.encoding import smart_text

from common.cast import str_to_uint


class SubmitAPIMixin:
    def render_json_on_post(self, request, form):
        if form.is_valid():
            solution = self.save_solution(form)
            response = {
                'submitted': True,
                'solutionId': solution.id,
                'attempts': self.get_limit_policy().get_attempt_message(solution.problem_id)
            }
        else:
            response = {
                'submitted': False,
                'errors': [smart_text(e) for errors in form.errors.values() for e in errors]
            }

        return JsonResponse(response, json_dumps_params={'ensure_ascii': False})


class AttemptsLeftAPIMixin:
    def render_json_on_get(self, request):
        problem_id = str_to_uint(request.GET.get('problem'))
        response = {
            'message': self.get_limit_policy().get_attempt_message(problem_id)
        }

        return JsonResponse(response, json_dumps_params={'ensure_ascii': False})
