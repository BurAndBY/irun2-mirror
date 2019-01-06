from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import generic

from common.cast import make_int_list_quiet
from users.models import UserProfile

from quizzes.forms import ShareCategoryForm
from quizzes.models import (
    AccessMode,
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


class CategoryAccessView(QuizAdminMixin, CategoryMixin, generic.base.ContextMixin, generic.View):
    tab = Tabs.CATEGORIES
    template_name = 'quizzes/category_access.html'
    requirements = CategoryPermissions.MANAGE_ACCESS

    def _load_access_control_list(self):
        return CategoryAccess.objects.filter(category=self.category).order_by('id').all()

    def get(self, request):
        share_form = ShareCategoryForm()
        context = self.get_context_data(
            share_form=share_form,
            acl=self._load_access_control_list(),
        )
        return render(request, self.template_name, context)

    def post(self, request):
        share_form = ShareCategoryForm()
        success = False

        if 'grant' in request.POST:
            share_form = ShareCategoryForm(request.POST)

            if share_form.is_valid():
                user_id = share_form.cleaned_data['user']
                CategoryAccess.objects.update_or_create(
                    category_id=self.category.id,
                    user_id=user_id,
                    defaults={
                        'mode': share_form.cleaned_data['mode'],
                        'who_granted': self.request.user,
                    }
                )
                UserProfile.objects.filter(pk=user_id).update(has_access_to_quizzes=True)
                success = True

        elif 'revoke' in request.POST:
            access_ids = make_int_list_quiet(request.POST.getlist('id'))
            CategoryAccess.objects.filter(category=self.category).filter(pk__in=access_ids).delete()
            success = True

        if success:
            return redirect('quizzes:categories:access', self.category.slug)

        context = self.get_context_data(
            share_form=share_form,
            acl=self._load_access_control_list(),
        )
        return render(request, self.template_name, context)
