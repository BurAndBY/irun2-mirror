from django.shortcuts import get_object_or_404
from cauth.mixins import UserPassesTestMixin
from common.access import Permissions, PermissionCheckMixin

from quizzes.constants import NO_CATEGORY_SLUG
from quizzes.tabs import Tabs
from quizzes.models import (
    AccessMode,
    Category,
    CategoryAccess,
    QuestionGroup,
)


class QuizAdminMixin(UserPassesTestMixin):
    tab = None

    def get_context_data(self, **kwargs):
        context = super(QuizAdminMixin, self).get_context_data(**kwargs)
        context['all_tabs'] = Tabs.ALL
        context['active_tab'] = self.tab
        return context

    def test_func(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff or user.userprofile.has_access_to_quizzes:
                return True
        return False


class CategoryPermissions(Permissions):
    EDIT_QUESTIONS = 1 << 0
    EDIT_PROPERTIES = 1 << 1
    MANAGE_ACCESS = 1 << 2
    ALL = EDIT_QUESTIONS | EDIT_PROPERTIES | MANAGE_ACCESS


class FetchCategoryMixin(object):
    def dispatch(self, request, categ_slug, *args, **kwargs):
        if categ_slug == NO_CATEGORY_SLUG:
            self.category = None
        else:
            self.category = get_object_or_404(Category, slug=categ_slug)
        return super(FetchCategoryMixin, self).dispatch(request, *args, **kwargs)

    @property
    def category_slug(self):
        return self.category.slug if self.category is not None else NO_CATEGORY_SLUG

    def get_context_data(self, **kwargs):
        context = super(FetchCategoryMixin, self).get_context_data(**kwargs)
        context['category'] = self.category
        context['category_slug'] = self.category_slug
        return context


class CategoryPermissionCheckMixin(PermissionCheckMixin):
    '''
    Must be placed afer FetchCategoryMixin
    '''
    def _make_permissions(self, user):
        if user.is_staff:
            return CategoryPermissions(CategoryPermissions.ALL)
        if user.userprofile.has_access_to_quizzes:
            access = CategoryAccess.objects.filter(category=self.category, user=user).first()
            if access is not None:
                if access.mode == AccessMode.READ:
                    return CategoryPermissions()
                elif access.mode == AccessMode.WRITE:
                    return CategoryPermissions(CategoryPermissions.EDIT_PROPERTIES | CategoryPermissions.EDIT_QUESTIONS)


class CategoryMixin(FetchCategoryMixin, CategoryPermissionCheckMixin):
    pass


class FetchQuestionGroupMixin(object):
    '''
    Must be placed after FetchCategoryMixin.
    '''
    def dispatch(self, request, group_id, *args, **kwargs):
        self.group = get_object_or_404(QuestionGroup, id=group_id, category=self.category)
        return super(FetchQuestionGroupMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FetchQuestionGroupMixin, self).get_context_data(**kwargs)
        context['group'] = self.group
        return context


class QuestionGroupMixin(FetchCategoryMixin, CategoryPermissionCheckMixin, FetchQuestionGroupMixin):
    pass
