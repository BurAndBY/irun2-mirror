from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic

import storage.utils as fsutils
from common.views import IRunnerPaginatedList

import forms
import models


class NewFeedbackView(generic.View):
    @staticmethod
    def _form_class(request):
        # for anonymous users we do not allow uploading files
        return forms.FeedbackFormWithUpload if request.user.is_authenticated() else forms.FeedbackForm

    def get(self, request):
        Form = NewFeedbackView._form_class(request)

        if request.user.is_authenticated():
            # extract email from user profile
            initial = {}
            if request.user.email is not None:
                initial['email'] = request.user.email
            form = Form(initial=initial)
        else:
            form = Form()

        return render(request, 'feedback/new.html', {'form': form})

    def post(self, request):
        Form = NewFeedbackView._form_class(request)

        form = Form(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)

            if request.user.is_authenticated():
                message.author = request.user
                message.attachment = fsutils.store_with_metadata(form.cleaned_data['upload'])

            message.save()
            return redirect('feedback:thanks')

        return render(request, 'feedback/new.html', {'form': form})


class FeedbackThanksView(generic.View):
    def get(self, request):
        return render(request, 'feedback/thanks.html', {})


class ListFeedbackView(IRunnerPaginatedList):
    model = models.FeedbackMessage
    template_name = 'feedback/list.html'
    paginate_by = 7

    def get_queryset(self):
        return ListFeedbackView.model.objects.order_by('-when')


class FeedbackDownloadView(generic.View):
    def get(self, request, message_id, filename):
        message = get_object_or_404(models.FeedbackMessage, pk=message_id)
        if message.attachment is None:
            raise Http404()
        if message.attachment.filename != filename:
            raise Http404()

        return fsutils.serve_resource_metadata(request, message.attachment)


class FeedbackDeleteView(generic.DeleteView):
    model = models.FeedbackMessage
    template_name = 'feedback/confirm.html'
    success_url = reverse_lazy('feedback:list')
