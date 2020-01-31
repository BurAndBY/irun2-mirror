from django.views import generic
from django.urls import reverse

from cauth.mixins import StaffMemberRequiredMixin

from .models import NewsMessage


class ListMessagesView(StaffMemberRequiredMixin, generic.ListView):
    template_name = 'news/index.html'

    def get_queryset(self):
        return NewsMessage.objects.all().order_by('-when')


class CreateMessageView(StaffMemberRequiredMixin, generic.CreateView):
    model = NewsMessage
    template_name = 'news/new.html'
    fields = ['subject', 'body', 'is_public']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(CreateMessageView, self).form_valid(form)

    def get_success_url(self):
        return reverse('news:list')


class UpdateMessageView(StaffMemberRequiredMixin, generic.UpdateView):
    model = NewsMessage
    template_name = 'news/update.html'
    fields = ['subject', 'body', 'is_public']

    def get_success_url(self):
        return reverse('news:list')


class ShowMessageView(generic.DetailView):
    template_name = 'news/show.html'

    def get_queryset(self):
        return NewsMessage.objects.filter(is_public=True)
