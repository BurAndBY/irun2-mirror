from django.views import generic

from .utils import IRunnerPaginator


class IRunnerBaseListView(generic.list.MultipleObjectMixin, generic.View):
    allow_all = True
    paginate_by = 25
    show_total_count = True

    def get_context_data(self, **kwargs):
        queryset = kwargs.pop('object_list', self.object_list)
        p = IRunnerPaginator(self.paginate_by, self.allow_all, self.show_total_count)
        context = p.paginate(self.request, queryset)
        context.update(**kwargs)
        return super(generic.list.MultipleObjectMixin, self).get_context_data(**context)

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)


class IRunnerListView(generic.list.MultipleObjectTemplateResponseMixin, IRunnerBaseListView):
    pass
