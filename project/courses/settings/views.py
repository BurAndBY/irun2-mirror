from collections import namedtuple

from django.urls import reverse
from django.db import transaction
from django.db.models import Count
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext_lazy as _

from common.bulk.update import change_rowset_3p, change_rowset_ordered_3p, notify_users_changed
from common.cacheutils import AllObjectsCache
from common.tree.fields import FOLDER_ID_PLACEHOLDER
from problems.models import ProblemFolder
from proglangs.models import Compiler
from quizzes.models import QuizInstance

from courses.settings.forms import (
    AccessForm,
    ActivityForm,
    CompilersForm,
    CourseCommonProblemsForm,
    CourseUsersForm,
    PropertiesForm,
    QueueForm,
    QuizInstanceCreateForm,
    QuizInstanceUpdateForm,
    SubgroupForm,
    TopicForm,
)
from courses.settings.forms import (
    ThreePanelProblemMultipleChoiceField,
    ThreePanelUserMultipleChoiceField,
)
from courses.settings.forms import create_member_subgroup_formset_class
from courses.models import (
    Course,
    Membership,
    TopicCommonProblem,
)
from courses.services import CourseDescr
from courses.views import BaseCourseView


class CourseSettingsView(BaseCourseView):
    tab = 'settings'

    def is_allowed(self, permissions):
        return permissions.settings


class CourseSettingsPropertiesView(CourseSettingsView):
    subtab = 'properties'
    template_name = 'courses/settings/properties.html'

    def get(self, request, course):
        form = PropertiesForm(instance=course)

        context = self.get_context_data(form=form, can_delete=True)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = PropertiesForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:settings:properties', course_id=course.id)

        context = self.get_context_data(form=form, can_delete=True)
        return render(request, self.template_name, context)


class CourseSettingsAccessView(CourseSettingsView):
    subtab = 'access'
    template_name = 'courses/settings/properties.html'

    def get(self, request, course):
        form = AccessForm(instance=course, user=request.user)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = AccessForm(request.POST, instance=course, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('courses:settings:access', course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class CourseSettingsCompilersView(CourseSettingsView):
    subtab = 'compilers'
    template_name = 'courses/settings/compilers.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsCompilersView, self).get_context_data(**kwargs)
        context['compiler_cache'] = AllObjectsCache(Compiler.objects.all())
        return context

    def get(self, request, course):
        form = CompilersForm(instance=course)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = CompilersForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:settings:compilers', course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


'''
Users
'''

UserFormPair = namedtuple('UserFormPair', 'user form')
RoleUsersViewModel = namedtuple('RoleUsersViewModel', 'name_singular name_plural url_pattern pairs formset')


class CourseSettingsUsersView(CourseSettingsView):
    subtab = 'users'
    template_name = 'courses/settings/users.html'

    def _make_view_model(self, role, name_singular, name_plural, url_pattern, data, subgroups):
        queryset = Membership.objects.filter(course=self.course, role=role).\
            select_related('user').order_by('user__last_name')
        formset_class = create_member_subgroup_formset_class(subgroups)
        formset = formset_class(queryset=queryset, data=data, prefix=str(role))
        pairs = [UserFormPair(membership.user, form) for membership, form in zip(queryset, formset)]

        return RoleUsersViewModel(name_singular, name_plural, url_pattern, pairs, formset)

    def _make_view_models(self, data=None):
        subgroups = self.course.subgroup_set.all().order_by('id')
        return [
            self._make_view_model(Membership.STUDENT, _('Student'), _('Students'),
                                  'courses:settings:users_students', data, subgroups),
            self._make_view_model(Membership.TEACHER, _('Teacher'), _('Teachers'),
                                  'courses:settings:users_teachers', data, subgroups),
        ]

    def get(self, request, course):
        view_models = self._make_view_models()
        context = self.get_context_data(view_models=view_models)
        return render(request, self.template_name, context)

    def post(self, request, course):
        view_models = self._make_view_models(request.POST)
        if all(view_model.formset.is_valid() for view_model in view_models):
            with transaction.atomic():
                for view_model in view_models:
                    view_model.formset.save()
            return redirect('courses:settings:users', course.id)

        context = self.get_context_data(view_models=view_models)
        return render(request, self.template_name, context)


class CourseSettingsUsersCommonView(CourseSettingsView):
    subtab = 'users'
    template_name = 'courses/settings/users_edit.html'

    def get_role(self):
        raise NotImplementedError()

    def _list_users(self, course):
        return list(course.members.filter(membership__role=self.get_role()).order_by('last_name'))

    def _make_form(self, course, data=None):
        form = CourseUsersForm(data)
        form.fields['users'].configure(
            initial=self._list_users(course),
            user=self.request.user,
            url_template=reverse('courses:settings:users_json_list', args=(course.id, FOLDER_ID_PLACEHOLDER))
        )
        return form

    def get(self, request, course):
        form = self._make_form(course)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = self._make_form(course, request.POST)
        if form.is_valid():
            with transaction.atomic():
                diff = change_rowset_3p(form.cleaned_data['users'], Membership, 'user_id', {'role': self.get_role(), 'course': course})
            notify_users_changed(request, diff)
            return redirect('courses:settings:users', course.id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class CourseSettingsUsersStudentsView(CourseSettingsUsersCommonView):
    def get_role(self):
        return Membership.STUDENT

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsUsersStudentsView, self).get_context_data(**kwargs)
        context['role'] = 'students'
        return context


class CourseSettingsUsersTeachersView(CourseSettingsUsersCommonView):
    def get_role(self):
        return Membership.TEACHER

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsUsersTeachersView, self).get_context_data(**kwargs)
        context['role'] = 'teachers'
        return context


class CourseSettingsUsersJsonListView(CourseSettingsView):
    def get(self, request, course, folder_id):
        return ThreePanelUserMultipleChoiceField.ajax(request.user, folder_id)


'''
Base views to view and edit course-to-many relationships in course settings.
'''


class CourseSettingsBaseListView(CourseSettingsView):
    '''
    You should:
    * set subtab
    * set template_name
    * override get_queryset()
    '''

    def get_queryset(self, course):
        raise NotImplementedError()

    def get(self, request, course):
        object_list = self.get_queryset(course)
        context = self.get_context_data(object_list=object_list)
        self._do_init_context(course, object_list, context)
        return render(request, self.template_name, context)

    def _do_init_context(self, course, object_list, context):
        # you can fill pass some additional calculated data to context
        pass


class CourseSettingsBaseCreateView(CourseSettingsView):
    '''
    You should:
    * set subtab
    * set form_class
    * set list_url_name
    '''
    template_name = 'courses/settings/component.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsBaseCreateView, self).get_context_data(**kwargs)
        context['cancel_url'] = reverse(self.list_url_name, args=(self.course.id,))
        return context

    def get(self, request, course):
        form = self.form_class(**self._extra_form_kwargs())
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = self.form_class(request.POST, **self._extra_form_kwargs())
        if form.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.course = course
                obj.save()
                form.save_m2m()
                self._do_save(course, form, obj)
            return redirect(self.list_url_name, course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def _do_save(self, course, form, obj):
        # you can do something after object has been saved (in the same transaction)
        pass

    def _extra_form_kwargs(self):
        return {}


class CourseSettingsBaseUpdateView(CourseSettingsView):
    '''
    You should:
    * set subtab
    * set form_class
    * set list_url_name
    '''
    template_name = 'courses/settings/component.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsBaseUpdateView, self).get_context_data(**kwargs)
        context['cancel_url'] = reverse(self.list_url_name, args=(self.course.id,))
        context['can_delete'] = True
        return context

    def _get_object(self, course_id, pk):
        model = self.form_class.Meta.model
        return get_object_or_404(model, course_id=course_id, pk=pk)

    def get(self, request, course, pk):
        obj = self._get_object(course.id, pk)
        form = self.form_class(instance=obj, **self._extra_form_kwargs())
        self._do_load(course, form, obj)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course, pk):
        obj = self._get_object(course, pk)
        form = self.form_class(request.POST, instance=obj, **self._extra_form_kwargs())

        if 'save' in request.POST:
            if form.is_valid():
                with transaction.atomic():
                    obj = form.save()
                    self._do_save(course, form, obj)
                return redirect(self.list_url_name, course_id=course.id)

        elif 'delete' in request.POST:
            obj.delete()
            return redirect(self.list_url_name, course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def _do_load(self, course, form, obj):
        pass

    def _do_save(self, course, form, obj):
        pass

    def _extra_form_kwargs(self):
        return {}


'''
Topics
'''


class TopicMixin(object):
    subtab = 'problems'
    form_class = TopicForm
    list_url_name = 'courses:settings:problems'

    def _extra_form_kwargs(self):
        return {'user': self.request.user}

    def _do_save(self, course, form, obj):
        target_num_problems = form.cleaned_data['num_problems']
        topic = obj

        slots = topic.slot_set.all()
        if len(slots) < target_num_problems:
            diff = target_num_problems - len(slots)
            for i in range(diff):
                topic.slot_set.create()
        else:
            for slot in slots[target_num_problems:]:
                slot.delete()

    def _do_load(self, course, form, obj):
        form.fields['num_problems'].initial = obj.slot_set.count()


class CourseSettingsProblemsView(TopicMixin, CourseSettingsView):
    template_name = 'courses/settings/problems.html'

    def get(self, request, course):
        course_descr = CourseDescr(course)
        folder_cache = AllObjectsCache(ProblemFolder.objects.annotate(problem_count=Count('problem')).all(), set(
            t.topic.problem_folder_id for t in course_descr.topic_descrs if t.topic.problem_folder_id is not None
        ))
        context = self.get_context_data(course_descr=course_descr, folder_cache=folder_cache)
        return render(request, self.template_name, context)


class CourseSettingsTopicsCreateView(TopicMixin, CourseSettingsBaseCreateView):
    pass


class CourseSettingsTopicsUpdateView(TopicMixin, CourseSettingsBaseUpdateView):
    pass


'''
Common problems
'''


class CourseSettingsCommonProblemsView(CourseSettingsView):
    template_name = 'courses/settings/common_problems_edit.html'

    def _make_form(self, course, data=None):
        form = CourseCommonProblemsForm(data)
        form.fields['common_problems'].configure(
            initial=course.get_common_problems(),
            user=self.request.user,
            url_template=reverse('courses:settings:problems_json_list', args=(course.id, FOLDER_ID_PLACEHOLDER))
        )
        return form

    def get(self, request, course):
        form = self._make_form(course)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = self._make_form(course, request.POST)
        if form.is_valid():
            Through = Course.common_problems.through
            with transaction.atomic():
                change_rowset_ordered_3p(form.cleaned_data['common_problems'], Through, 'problem_id', {'course': course})

            return redirect('courses:settings:problems', course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class CourseSettingsProblemsJsonListView(CourseSettingsView):
    def get(self, request, course, folder_id):
        return ThreePanelProblemMultipleChoiceField.ajax(request.user, folder_id)


class CourseSettingsTopicCommonProblemsView(CourseSettingsView):
    template_name = 'courses/settings/common_problems_edit.html'

    def _create_form(self, course, topic_id, data=None):
        topic = get_object_or_404(course.topic_set, pk=topic_id)
        form = CourseCommonProblemsForm(data)
        form.fields['common_problems'].configure(
            initial=topic.get_common_problems(),
            user=self.request.user,
            url_template=reverse('courses:settings:problems_json_list', args=(course.id, FOLDER_ID_PLACEHOLDER))
        )
        return form

    def get(self, request, course, topic_id):
        form = self._create_form(course, topic_id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course, topic_id):
        form = self._create_form(course, topic_id, request.POST)
        if form.is_valid():
            with transaction.atomic():
                change_rowset_ordered_3p(form.cleaned_data['common_problems'], TopicCommonProblem, 'problem_id', {'topic_id': topic_id})
            return redirect('courses:settings:problems', course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


'''
Sheet
'''


class SheetMixin(object):
    subtab = 'sheet'
    form_class = ActivityForm
    list_url_name = 'courses:settings:sheet'

    def _extra_form_kwargs(self):
        return {'course_id': self.course.id}


class CourseSettingsSheetActivityListView(SheetMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings/sheet.html'

    def get_queryset(self, course):
        return course.activity_set.all()

    def _do_init_context(self, course, object_list, context):

        sum_weights = 0.0
        main_activities = []
        extra_activities = []

        for activity in object_list:
            w = activity.weight
            sum_weights += w
            if w != 0.0:
                main_activities.append(activity)
            else:
                extra_activities.append(activity)

        context['main_activities'] = main_activities
        context['extra_activities'] = extra_activities

        EPS = 1.E-6
        TARGET_SUM = 1.0
        if (sum_weights > EPS) and (abs(sum_weights - TARGET_SUM) > EPS):
            context['sum_actual'] = sum_weights
            context['sum_expected'] = TARGET_SUM
            context['sum_is_bad'] = True


class CourseSettingsSheetActivityCreateView(SheetMixin, CourseSettingsBaseCreateView):
    pass


class CourseSettingsSheetActivityUpdateView(SheetMixin, CourseSettingsBaseUpdateView):
    pass


'''
Subgroups
'''


class SubroupMixin(object):
    subtab = 'subgroups'
    form_class = SubgroupForm
    list_url_name = 'courses:settings:subgroups'


class CourseSettingsSubgroupListView(SubroupMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings/subgroups.html'

    def get_queryset(self, course):
        return course.subgroup_set.all()


class CourseSettingsSubgroupCreateView(SubroupMixin, CourseSettingsBaseCreateView):
    pass


class CourseSettingsSubgroupUpdateView(SubroupMixin, CourseSettingsBaseUpdateView):
    pass


'''
Delete course
'''


class CourseSettingsDeleteView(CourseSettingsView):
    subtab = 'properties'
    template_name = 'courses/course_confirm_delete.html'

    def get(self, request, course):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, course):
        course.delete()
        return redirect('courses:index')


'''
Quizzes
'''


class QuizMixin(object):
    subtab = 'quizzes'
    list_url_name = 'courses:settings:quizzes'

    def get_context_data(self, **kwargs):
        context = super(QuizMixin, self).get_context_data(**kwargs)
        context['cancel_url'] = reverse(self.list_url_name, args=(self.course.id,))
        return context


class CourseSettingsQuizzesView(QuizMixin, CourseSettingsView):
    template_name = 'courses/settings/quizzes.html'

    def _make_view_model(self, data=None):
        formset_class = modelformset_factory(QuizInstance, fields=('is_available',))
        queryset = QuizInstance.objects.filter(course=self.course).select_related('quiz_template').order_by('id')
        formset = formset_class(data, queryset=queryset)
        pairs = zip(queryset, formset)
        return formset, pairs

    def get(self, request, course):
        formset, pairs = self._make_view_model()
        context = self.get_context_data(formset=formset, pairs=pairs)
        return render(request, self.template_name, context)

    def post(self, request, course):
        formset, pairs = self._make_view_model(request.POST)
        if formset.is_valid():
            formset.save()
            return redirect(self.list_url_name, course.id)

        context = self.get_context_data(formset=formset, pairs=pairs)
        return render(request, self.template_name, context)


class CourseSettingsQuizzesCreateView(QuizMixin, CourseSettingsView):
    template_name = 'courses/settings/component.html'

    def get(self, request, course):
        form = QuizInstanceCreateForm()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = QuizInstanceCreateForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.course = course
            instance.time_limit = instance.quiz_template.time_limit
            instance.attempts = instance.quiz_template.attempts
            instance.save()
            return redirect(self.list_url_name, course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class CourseSettingsQuizzesUpdateView(QuizMixin, CourseSettingsView):
    form_class = QuizInstanceUpdateForm
    template_name = 'courses/settings/quiz_edit.html'

    def _load_instance(self, instance_id):
        instance = QuizInstance.objects.filter(pk=instance_id, course=self.course).\
            select_related('quiz_template').\
            annotate(session_count=Count('quizsession')).\
            first()
        can_delete = (instance is not None) and (instance.session_count == 0)
        return instance, can_delete

    def get(self, request, course, instance_id):
        instance, can_delete = self._load_instance(instance_id)
        if instance is None:
            return redirect(self.list_url_name, course.id)

        form = self.form_class(instance=instance)
        context = self.get_context_data(instance=instance, can_delete=can_delete, form=form)
        return render(request, self.template_name, context)

    def post(self, request, course, instance_id):
        instance, can_delete = self._load_instance(instance_id)
        if instance is None:
            return redirect(self.list_url_name, course.id)

        if 'save' in request.POST:
            form = self.form_class(request.POST, instance=instance)
            if form.is_valid():
                form.save()
            else:
                context = self.get_context_data(instance=instance, can_delete=can_delete, form=form)
                return render(request, self.template_name, context)

        elif 'delete' in request.POST:
            if can_delete:
                instance.delete()

        return redirect(self.list_url_name, course.id)


'''
Electronic queue
'''


class QueueMixin(object):
    subtab = 'queues'
    form_class = QueueForm
    list_url_name = 'courses:settings:queues'


class CourseSettingsQueuesView(QueueMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings/queues.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsQueuesView, self).get_context_data(**kwargs)
        return context

    def get_queryset(self, course):
        return course.queue_set.annotate(num_entries=Count('queueentry'))


class CourseSettingsQueueCreateView(QueueMixin, CourseSettingsBaseCreateView):
    def _extra_form_kwargs(self):
        return {'course': self.course}


class CourseSettingsQueueUpdateView(QueueMixin, CourseSettingsBaseUpdateView):
    def _extra_form_kwargs(self):
        return {'course': self.course}
