import difflib

from django.views import generic
from django.shortcuts import render

from cauth.mixins import LoginRequiredMixin

from solutions.compare.forms import CompareSolutionsForm
from solutions.compare.loader import fetch_solution

'''
Compare two solutions
'''


class CompareSolutionsView(LoginRequiredMixin, generic.View):
    template_name = 'solutions/compare.html'

    def _get_compare_context(self, first_id, second_id, contextual_diff):
        first = fetch_solution(first_id, self.request.user)
        second = fetch_solution(second_id, self.request.user)
        ok = (first.text is not None) and (second.text is not None)
        context = {}
        context['first'] = first
        context['second'] = second
        context['has_error'] = not ok
        context['has_result'] = ok
        context['show_author'] = (first.solution.author_id != second.solution.author_id) if (first.solution is not None and second.solution is not None) else False
        context['full'] = not contextual_diff

        if ok:
            first_lines = first.text.splitlines()
            second_lines = second.text.splitlines()
            differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=None)
            html = differ.make_table(first_lines, second_lines, context=contextual_diff)
            html = html.replace('<td nowrap="nowrap">', '<td>')
            html = html.replace('&nbsp;', ' ')
            context['difflib_html_content'] = html

        return context

    def get(self, request):
        if request.GET:
            form = CompareSolutionsForm(request.GET)
            if form.is_valid():
                context = self._get_compare_context(form.cleaned_data['first'], form.cleaned_data['second'], form.cleaned_data['diff'])
                return render(request, self.template_name, context)
        else:
            form = CompareSolutionsForm()

        # fallback
        context = {'form': form}
        return render(request, self.template_name, context)
