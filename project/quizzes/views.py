from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from django.db import models, transaction
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

import json

from common.pageutils import paginate

from quizzes.serializers import QuestionDataSerializer, RelationsDataSerializer
from quizzes.forms import UploadFileForm
from quizzes.mixins import (
    QuizAdminMixin,
    CategoryMixin,
    QuestionGroupMixin,
    CategoryPermissions,
)
from quizzes.models import (
    Choice,
    GroupQuizRelation,
    Question,
    QuestionGroup,
    QuizSession,
    QuizTemplate,
)
from quizzes.tabs import Tabs
from quizzes.utils import finish_overdue_sessions, get_question_editor_language_tags, get_empty_question_data, \
    is_question_valid, add_questions_to_question_group, QUESTION_KINDS, QUESTION_KINDS_BY_ID, is_relation_valid
from quizzes.statistics import get_statistics


class EmptyView(QuizAdminMixin, generic.TemplateView):
    template_name = 'quizzes/base.html'


class QuestionGroupListView(QuizAdminMixin, CategoryMixin, generic.ListView):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/question_group_list.html'

    def get_queryset(self):
        # count related non-deleted questions
        queryset = QuestionGroup.objects.filter(category=self.category).annotate(question_count=models.Sum(
            models.Case(
                models.When(question__is_deleted=False, then=1),
                default=0,
                output_field=models.IntegerField()
            ))
        ).order_by('id')
        return queryset


class QuestionGroupBrowseView(QuizAdminMixin, QuestionGroupMixin, generic.TemplateView):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/question_group_browse.html'
    paginate_by = 7

    def get_context_data(self, **kwargs):
        context = super(QuestionGroupBrowseView, self).get_context_data(**kwargs)

        # fetch related non-deleted questions
        qs = self.group.question_set.filter(is_deleted=False).order_by('id')

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
    fields = ['name', 'shuffle_questions', 'score_policy', 'attempts', 'time_limit']

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


class QuizTemplateEditGroupsView(QuizAdminMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.TEMPLATES
    template_name = 'quizzes/quiz_template_edit_groups.html'
    model = QuizTemplate

    def _process_error(self, request, quiz_template, json_data):
        context = self.get_context_data()
        context['has_error'] = True
        context['relations'] = json.dumps(json_data)
        groups = QuestionGroup.objects.all()
        json_groups = [{'id': group.id, 'name': group.name} for group in groups]
        context['groups'] = json.dumps(json_groups)
        context['object'] = quiz_template
        return render(request, self.template_name, context)

    def _get_data(self, pk):
        quiz_template = get_object_or_404(QuizTemplate, pk=pk)
        context = self.get_context_data()
        context['object'] = quiz_template
        relations = GroupQuizRelation.objects.filter(template=quiz_template).select_related('group')
        json_relations = [{'id': rel.group_id, 'name': rel.group.name, 'points': rel.points} for rel in relations]
        groups = QuestionGroup.objects.all()
        json_groups = [{'id': group.id, 'name': group.name} for group in groups]
        context['relations'] = json.dumps(json_relations)
        context['groups'] = json.dumps(json_groups)
        return context

    def get(self, request, pk):
        return render(request, self.template_name, self._get_data(pk))

    def post(self, request, pk):
        quiz_template = get_object_or_404(QuizTemplate, pk=pk)
        try:
            json_data = json.loads(request.POST['relations'])
        except:
            return redirect('quizzes:templates:detail', pk)

        serializer = RelationsDataSerializer(data={'rels': json_data})
        if not serializer.is_valid(raise_exception=False):
            return self._process_error(request, quiz_template, json_data)

        rels_data = serializer.save().rels
        for rel in rels_data:
            if not is_relation_valid(rel):
                return self._process_error(request, quiz_template, json_data)

        with transaction.atomic():
            GroupQuizRelation.objects.filter(template_id=pk).delete()
            rels = []
            for i, r in enumerate(rels_data):
                rels.append(GroupQuizRelation(template=quiz_template, group_id=r.id, points=r.points, order=i + 1))
            GroupQuizRelation.objects.bulk_create(rels)

        return redirect('quizzes:templates:detail', pk)


class QuizSessionListView(QuizAdminMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.TEMPLATES
    paginate_by = 25
    template_name = 'quizzes/quiz_template_sessions.html'

    def get(self, request, pk):
        active_sessions = QuizSession.objects.filter(quiz_instance__quiz_template_id=pk, is_finished=False)
        finish_overdue_sessions(active_sessions)

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


class QuizStatisticsView(QuizAdminMixin, generic.base.ContextMixin, generic.View):
    template_name = 'quizzes/quiz_template_statistics.html'

    def get(self, request, pk):
        quiz_template = get_object_or_404(QuizTemplate, pk=pk)

        context = self.get_context_data()
        context['object'] = quiz_template

        statistics = get_statistics(pk)
        context['statistics'] = json.dumps(statistics)
        context['has_data'] = statistics is not None
        context['has_previous_year'] = 'by-stud-group-prev' in statistics
        return render(request, self.template_name, context)


class SaveQuestionMixin(object):
    def _process_error(self, request, json_data):
        context = self.get_context_data()
        context['has_error'] = True
        context['object'] = json.dumps(json_data)
        context['languageTags'] = json.dumps(get_question_editor_language_tags())
        return render(request, self.template_name, context)

    def _redirect_to_list(self):
        return redirect('quizzes:categories:groups:browse', self.category_slug, self.group.id)

    def _do_post(self, request):
        try:
            json_data = json.loads(request.POST['question'])
        except:
            return self._redirect_to_list()

        serializer = QuestionDataSerializer(data=json_data)
        if not serializer.is_valid(raise_exception=False):
            return self._process_error(request, json_data)

        question_data = serializer.save()
        if not is_question_valid(question_data):
            return self._process_error(request, json_data)

        with transaction.atomic():
            if question_data.id is not None:
                question = get_object_or_404(Question, pk=question_data.id)
                question.is_deleted = True
                question.save()
            question = Question.objects.create(kind=QUESTION_KINDS[question_data.type],
                                               text=question_data.text, group=self.group)
            choices = []
            for c in question_data.choices:
                choices.append(Choice(question=question, text=c.text, is_right=c.is_right))
            Choice.objects.bulk_create(choices)

        return self._redirect_to_list()


class QuestionEditView(QuizAdminMixin, QuestionGroupMixin, SaveQuestionMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/question_edit.html'
    requirements = CategoryPermissions.EDIT_QUESTIONS

    def _get_question_data(self, question_id):
        question = get_object_or_404(Question, pk=question_id, group=self.group)
        choices = []
        for c in question.choice_set.all():
            choices.append({'id': c.id, 'text': c.text, 'is_right': c.is_right})
        return {'id': question.id, 'text': question.text,
                'type': QUESTION_KINDS_BY_ID[question.kind], 'choices': choices}

    def get(self, request, question_id):
        context = self.get_context_data()
        context['object'] = json.dumps(self._get_question_data(question_id))
        context['languageTags'] = json.dumps(get_question_editor_language_tags())
        return render(request, self.template_name, context)

    def post(self, request, question_id):
        return self._do_post(request)


class QuestionCreateView(QuizAdminMixin, QuestionGroupMixin, generic.base.ContextMixin, SaveQuestionMixin, generic.View):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/question_edit.html'
    requirements = CategoryPermissions.EDIT_QUESTIONS

    def get(self, request):
        any_question = Question.objects.filter(group=self.group, is_deleted=False).first()
        kind = Question.SINGLE_ANSWER if any_question is None else any_question.kind

        context = self.get_context_data()
        context['object'] = json.dumps(get_empty_question_data(kind))
        context['languageTags'] = json.dumps(get_question_editor_language_tags())
        return render(request, self.template_name, context)

    def post(self, request):
        return self._do_post(request)


class QuestionGroupCreateView(QuizAdminMixin, CategoryMixin, generic.CreateView):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/question_group_create.html'
    requirements = CategoryPermissions.EDIT_QUESTIONS

    model = QuestionGroup
    fields = ['name']

    def get_success_url(self):
        return reverse('quizzes:categories:groups:browse', kwargs={'categ_slug': self.category_slug, 'group_id': self.object.id})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.category = self.category
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class QuestionGroupUploadFromFileView(QuizAdminMixin, QuestionGroupMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/question_group_upload.html'
    requirements = CategoryPermissions.EDIT_QUESTIONS

    def _process_error(self, request):
        context = self.get_context_data(error='ERROR', form=UploadFileForm())
        return render(request, self.template_name, context)

    def get(self, request):
        form = UploadFileForm()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        questions_data = []
        if form.is_valid():
            json_data = request.FILES['file'].read()
            try:
                json_questions = json.loads(json_data)
            except:
                return self._process_error(request)
            for q in json_questions:
                serializer = QuestionDataSerializer(data=q)
                if not serializer.is_valid(raise_exception=False):
                    return self._process_error(request)
                question_data = serializer.save()
                if not is_question_valid(question_data):
                    return self._process_error(request)
                questions_data.append(question_data)
        else:
            return self._process_error(request)

        add_questions_to_question_group(self.group, questions_data)
        return redirect('quizzes:categories:groups:browse', self.category_slug, self.group.id)
