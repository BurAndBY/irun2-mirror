from django.shortcuts import render
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin

from .tabs import Tabs


class QuizAdminMixin(StaffMemberRequiredMixin):
    tab = None

    def get_context_data(self, **kwargs):
        context = {
            'all_tabs': Tabs.ALL,
            'active_tab': self.tab,
        }
        context.update(kwargs)
        return context


class EmptyView(QuizAdminMixin, generic.TemplateView):
    template_name = 'quizzes/base.html'


class QuestionGroupListView(QuizAdminMixin, generic.TemplateView):
    tab = Tabs.GROUPS
    template_name = 'quizzes/base.html'


class QuizTemplateListView(QuizAdminMixin, generic.TemplateView):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/base.html'
