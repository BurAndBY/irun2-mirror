from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.db import models, transaction
from django.core.urlresolvers import reverse

from cauth.mixins import StaffMemberRequiredMixin
from common.pageutils import paginate

from .forms import AddQuestionGroupForm
from .models import QuestionGroup, QuizTemplate, GroupQuizRelation, QuizSession
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


class QuizTemplateListView(QuizAdminMixin, generic.ListView):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/quiz_template_list.html'
    model = QuizTemplate

    def get_queryset(self):
        return QuizTemplate.objects.annotate(num_sessions=models.Count('quizinstance__quizsession'))


class QuizTemplateCreateView(QuizAdminMixin, generic.CreateView):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/quiz_template_create.html'
    model = QuizTemplate
    fields = ['name']

    def get_success_url(self):
        return reverse('quizzes:templates:list')


class QuizTemplateUpdateView(QuizAdminMixin, generic.UpdateView):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/quiz_template_update.html'
    model = QuizTemplate
    fields = ['name', 'shuffle_questions', 'attempts', 'time_limit']

    def get_success_url(self):
        return reverse('quizzes:templates:detail', kwargs={'pk': self.object.id})


class QuizTemplateDetailView(QuizAdminMixin, generic.DetailView):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/quiz_template_detail.html'
    model = QuizTemplate

    def get_context_data(self, **kwargs):
        context = super(QuizTemplateDetailView, self).get_context_data(**kwargs)
        context['relations'] = GroupQuizRelation.objects.filter(template=self.object).select_related('group')
        return context


class QuizTemplateAddGroupView(QuizAdminMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/quiz_template_add_group.html'
    model = GroupQuizRelation
    fields = ['group', 'points']

    def get_success_url(self):
        return reverse('quizzes:templates:detail', kwargs={'pk': self.object.id})

    def get(self, request, pk):
        quiz_template = get_object_or_404(QuizTemplate, pk=pk)
        form = AddQuestionGroupForm(instance=GroupQuizRelation(template=quiz_template))
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, pk):
        quiz_template = get_object_or_404(QuizTemplate, pk=pk)
        form = AddQuestionGroupForm(request.POST, instance=GroupQuizRelation(template=quiz_template))
        if form.is_valid():
            with transaction.atomic():
                relation = form.save(commit=False)
                count = GroupQuizRelation.objects.filter(template=quiz_template).count()
                relation.order = count + 1
                relation.save()
            return redirect('quizzes:templates:detail', pk)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class QuizSessionListView(QuizAdminMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.TEMPLATES
    paginate_by = 25
    template_name = 'quizzes/quiz_template_sessions.html'

    def get(self, request, pk):
        context = self.get_context_data()
        template = QuizTemplate.objects.filter(pk=pk).first()
        if template is None:
            return redirect('quizzes:templates:list')

        queryset = QuizSession.objects.\
            filter(quiz_instance__quiz_template=template).\
            select_related('quiz_instance__course').\
            select_related('quiz_instance').\
            select_related('user').\
            order_by('-start_time')

        page_context = paginate(request, queryset, self.paginate_by, allow_all=False)
        context.update(page_context)
        context['template'] = template
        return render(request, self.template_name, context)
