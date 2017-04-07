from django.shortcuts import render
from django.views import generic
from django.db import models

from cauth.mixins import StaffMemberRequiredMixin
from common.pageutils import paginate

from .models import QuestionGroup
from .tabs import Tabs


class QuizAdminMixin(StaffMemberRequiredMixin):
    tab = None

    def get_context_data(self, **kwargs):
        context = super(QuizAdminMixin, self).get_context_data(**kwargs)
        context['all_tabs'] = Tabs.ALL
        context['active_tab'] = self.tab
        context.update(kwargs)
        return context


class EmptyView(QuizAdminMixin, generic.TemplateView):
    template_name = 'quizzes/base.html'


class QuestionGroupListView(QuizAdminMixin, generic.ListView):
    tab = Tabs.GROUPS
    template_name = 'quizzes/question_group_list.html'

    # count related non-deleted questions
    queryset = QuestionGroup.objects.annotate(question_count=models.Sum(
        models.Case(
            models.When(question__is_deleted=False, then=1),
            default=0,
            output_field=models.IntegerField()
        ))
    ).order_by('id')


class QuestionGroupBrowseView(QuizAdminMixin, generic.DetailView):
    tab = Tabs.GROUPS
    model = QuestionGroup
    template_name = 'quizzes/question_group_browse.html'
    paginate_by = 7

    def get_context_data(self, **kwargs):
        context = super(QuestionGroupBrowseView, self).get_context_data(**kwargs)

        # fetch related non-deleted questions
        qs = self.object.question_set.filter(is_deleted=False).order_by('id')

        page_context = paginate(self.request, qs, default_page_size=self.paginate_by, allow_all=False)
        context.update(page_context)
        return context


class QuizTemplateListView(QuizAdminMixin, generic.TemplateView):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/base.html'
