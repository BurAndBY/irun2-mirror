from django.urls import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import generic

from cauth.acl.accessmode import AccessMode
from cauth.acl.mixins import ShareWithUserMixin
from common.cast import make_int_list_quiet
from users.models import UserProfile

from cauth.acl.forms import ShareWithUserForm
from quizzes.models import (
    Category,
    CategoryAccess,
)
from quizzes.tabs import Tabs
from quizzes.mixins import (
    CategoryPermissions,
    QuizAdminMixin,
    CategoryMixin,
)
from quizzes.constants import NO_CATEGORY_SLUG


class CategoryListView(QuizAdminMixin, generic.ListView):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/category_list.html'

    model = Category

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        if self.request.user.is_staff:
            context['no_category_slug'] = NO_CATEGORY_SLUG
        return context

    def get_queryset(self):
        queryset = super(CategoryListView, self).get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(categoryaccess__user=self.request.user)
        return queryset


class CategoryCreateView(QuizAdminMixin, generic.CreateView):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/category_create.html'

    model = Category
    fields = ['name', 'slug']

    def get_success_url(self):
        return reverse('quizzes:categories:list')

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            CategoryAccess.objects.create(category=self.object, user=self.request.user, mode=AccessMode.WRITE)
        return HttpResponseRedirect(self.get_success_url())


class CategoryUpdateView(QuizAdminMixin, CategoryMixin, generic.UpdateView):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/category_update.html'
    requirements = CategoryPermissions.EDIT_PROPERTIES

    model = Category
    fields = ['name', 'slug']

    def get_success_url(self):
        return reverse('quizzes:categories:groups:list', kwargs={'categ_slug': self.category.slug})

    def get_object(self):
        return self.category


class CategoryAccessView(QuizAdminMixin, CategoryMixin, ShareWithUserMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/category_access.html'
    requirements = CategoryPermissions.MANAGE_ACCESS
    access_model = CategoryAccess
    access_model_object_field = 'category'
    userprofile_model_field = 'has_access_to_quizzes'

    def get(self, request):
        context = self._get(request, self.category)
        return render(request, self.template_name, self.get_context_data(**context))

    def post(self, request):
        success, context = self._post(request, self.category)
        if success:
            return redirect('quizzes:categories:access', self.category.slug)
        return render(request, self.template_name, self.get_context_data(**context))
