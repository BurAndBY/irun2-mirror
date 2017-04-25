from collections import namedtuple

from django.contrib import auth, messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from common.cacheutils import AllObjectsCache
from proglangs.models import Compiler
from problems.models import Problem

from forms import TopicForm, ActivityForm, PropertiesForm, CompilersForm, CourseUsersForm, CourseCommonProblemsForm, SubgroupForm, AccessForm, \
    QuizInstanceCreateForm, QuizInstanceUpdateForm
from forms import TwoPanelUserMultipleChoiceField, TwoPanelProblemMultipleChoiceField
from forms import create_member_subgroup_formset_class
from models import Membership
from quizzes.models import QuizInstance
from views import BaseCourseView


class CourseSettingsView(BaseCourseView):
    tab = 'settings'

    def is_allowed(self, permissions):
        return permissions.settings


class CourseSettingsPropertiesView(CourseSettingsView):
    subtab = 'properties'
    template_name = 'courses/settings_properties.html'

    def get(self, request, course):
        form = PropertiesForm(instance=course)

        context = self.get_context_data(form=form, can_delete=True)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = PropertiesForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_settings_properties', course_id=course.id)

        context = self.get_context_data(form=form, can_delete=True)
        return render(request, self.template_name, context)


class CourseSettingsAccessView(CourseSettingsView):
    subtab = 'access'
    template_name = 'courses/settings_properties.html'

    def get(self, request, course):
        form = AccessForm(instance=course)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = AccessForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_settings_access', course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class CourseSettingsCompilersView(CourseSettingsView):
    subtab = 'compilers'
    template_name = 'courses/settings_compilers.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsCompilersView, self).get_context_data(**kwargs)
        context['compiler_cache'] = AllObjectsCache(Compiler)
        return context

    def get(self, request, course):
        form = CompilersForm(instance=course)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = CompilersForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_settings_compilers', course_id=course.id)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

'''
Users
'''

UserFormPair = namedtuple('UserFormPair', 'user form')
RoleUsersViewModel = namedtuple('RoleUsersViewModel', 'name_singular name_plural url_pattern pairs formset')


class CourseSettingsUsersView(CourseSettingsView):
    subtab = 'users'
    template_name = 'courses/settings_users.html'

    def _make_view_model(self, role, name_singular, name_plural, url_pattern, data, subgroups):
        queryset = Membership.objects.filter(course=self.course, role=role).select_related('user').order_by('user__last_name')
        formset_class = create_member_subgroup_formset_class(subgroups)
        formset = formset_class(queryset=queryset, data=data, prefix=str(role))
        pairs = [UserFormPair(membership.user, form) for membership, form in zip(queryset, formset)]

        return RoleUsersViewModel(name_singular, name_plural, url_pattern, pairs, formset)

    def _make_view_models(self, data=None):
        subgroups = self.course.subgroup_set.all().order_by('id')
        return [
            self._make_view_model(Membership.STUDENT, _('Student'), _('Students'), 'courses:course_settings_users_students', data, subgroups),
            self._make_view_model(Membership.TEACHER, _('Teacher'), _('Teachers'), 'courses:course_settings_users_teachers', data, subgroups),
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
            return redirect('courses:course_settings_users', course.id)

        context = self.get_context_data(view_models=view_models)
        return render(request, self.template_name, context)


class CourseSettingsUsersCommonView(CourseSettingsView):
    subtab = 'users'
    template_name = 'courses/settings_users_edit.html'

    def get_role(self):
        raise NotImplementedError()

    def _list_users(self, course):
        return list(course.members.filter(membership__role=self.get_role()))

    def get(self, request, course):
        form = CourseUsersForm(initial={'users': self._list_users(course)})
        form.fields['users'].widget.url_params = [course.id]

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def _put_message(self, request, users_added, users_removed):
        msgs = []
        if users_added > 0:
            msg = ungettext(
                '%(count)d user was added.',
                '%(count)d users were added.',
                users_added) % {
                'count': users_added,
                }
            msgs.append(msg)
        if users_removed > 0:
            msg = ungettext(
                '%(count)d user was removed.',
                '%(count)d users were removed.',
                users_removed) % {
                'count': users_removed,
                }
            msgs.append(msg)
        if msgs:
            messages.add_message(request, messages.INFO, ' '.join(msgs))

    def post(self, request, course):
        role = self.get_role()
        present_users = self._list_users(course)
        present_ids = set(user.id for user in present_users)

        form = CourseUsersForm(request.POST, initial={'users': present_users})
        if form.is_valid():
            target_users = form.cleaned_data['users']
            target_ids = set(user.id for user in target_users)

            users_added = 0
            users_removed = 0

            with transaction.atomic():
                for user in present_users:
                    if user.id not in target_ids:
                        Membership.objects.filter(role=role, course=course, user=user).delete()
                        users_removed += 1

                for user in target_users:
                    if user.id not in present_ids:
                        Membership.objects.create(role=role, course=course, user=user)
                        users_added += 1

            self._put_message(request, users_added, users_removed)
            return redirect('courses:course_settings_users', course.id)

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
        users = auth.get_user_model().objects.filter(userprofile__folder_id=folder_id)
        return TwoPanelUserMultipleChoiceField.ajax(users)

'''
Subgroups
'''


class CourseSettingsSubgroupsView(CourseSettingsView):
    subtab = 'subgroups'
    template_name = 'courses/settings_subgroups.html'

    def get(self, request, course):
        context = self.get_context_data()
        return render(request, self.template_name, context)


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
    template_name = 'courses/settings_component.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsBaseCreateView, self).get_context_data(**kwargs)
        context['cancel_url'] = reverse(self.list_url_name, args=(self.course.id,))
        return context

    def get(self, request, course):
        form = self.form_class()
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = self.form_class(request.POST)
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


class CourseSettingsBaseUpdateView(CourseSettingsView):
    '''
    You should:
    * set subtab
    * set form_class
    * set list_url_name
    '''
    template_name = 'courses/settings_component.html'

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
        form = self.form_class(instance=obj)
        self._do_load(course, form, obj)

        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course, pk):
        obj = self._get_object(course, pk)
        form = self.form_class(request.POST, instance=obj)

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

'''
Topics
'''


class TopicMixin(object):
    subtab = 'problems'
    form_class = TopicForm
    list_url_name = 'courses:course_settings_problems'

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


class CourseSettingsProblemsView(TopicMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings_problems.html'

    def get_context_data(self, **kwargs):
        context = super(CourseSettingsProblemsView, self).get_context_data(**kwargs)
        context['common_problems'] = list(self.course.common_problems.all())
        return context

    def get_queryset(self, course):
        return course.topic_set.all().prefetch_related('slot_set')


class CourseSettingsTopicsCreateView(TopicMixin, CourseSettingsBaseCreateView):
    pass


class CourseSettingsTopicsUpdateView(TopicMixin, CourseSettingsBaseUpdateView):
    pass


'''
Common problems
'''


class CourseSettingsCommonProblemsView(CourseSettingsView):
    template_name = 'courses/settings_common_problems_edit.html'

    def get(self, request, course):
        form = CourseCommonProblemsForm(instance=course)
        form.fields['common_problems'].widget.url_params = [course.id]
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)

    def post(self, request, course):
        form = CourseCommonProblemsForm(request.POST, instance=course)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            return redirect('courses:course_settings_problems', course_id=course.id)
        context = self.get_context_data(form=form)
        return render(request, self.template_name, context)


class CourseSettingsProblemsJsonListView(CourseSettingsView):
    def get(self, request, course, folder_id):
        problems = Problem.objects.filter(folders__id=folder_id)
        return TwoPanelProblemMultipleChoiceField.ajax(problems)

'''
Sheet
'''


class SheetMixin(object):
    subtab = 'sheet'
    form_class = ActivityForm
    list_url_name = 'courses:course_settings_sheet'


class CourseSettingsSheetActivityListView(SheetMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings_sheet.html'

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
    list_url_name = 'courses:course_settings_subgroups'


class CourseSettingsSubgroupListView(SubroupMixin, CourseSettingsBaseListView):
    template_name = 'courses/settings_subgroups.html'

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
    list_url_name = 'courses:course_settings_quizzes'

    def get_context_data(self, **kwargs):
        context = super(QuizMixin, self).get_context_data(**kwargs)
        context['cancel_url'] = reverse(self.list_url_name, args=(self.course.id,))
        return context


class CourseSettingsQuizzesView(QuizMixin, CourseSettingsView):
    template_name = 'courses/settings_quizzes.html'

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
    template_name = 'courses/settings_component.html'

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
    template_name = 'courses/settings_quiz_edit.html'

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
