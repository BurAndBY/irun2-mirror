from django.contrib import messages
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import ungettext
from django.views import generic

from cauth.mixins import StaffMemberRequiredMixin
from problems.models import TestCase, ProblemRelatedFile, ProblemRelatedSourceFile
from solutions.models import Judgement, JudgementLog, Challenge, TestCaseResult

from .forms import TextOrUploadForm
from .models import FileMetadata
from .storage import create_storage, ResourceId
from .utils import parse_resource_id, serve_resource


class NewView(StaffMemberRequiredMixin, generic.FormView):
    template_name = 'storage/new.html'
    form_class = TextOrUploadForm

    def form_valid(self, form):
        upload = form.cleaned_data['upload']

        if upload is not None:
            f = upload
        else:
            text = form.cleaned_data['text']
            f = ContentFile(text.encode('utf-8'))

        storage = create_storage()
        resource_id = storage.save(f)

        return redirect('storage:show', str(resource_id))


class ShowView(StaffMemberRequiredMixin, generic.View):
    template_name = 'storage/show.html'

    def get(self, request, resource_id):
        resource_id = parse_resource_id(resource_id)

        storage = create_storage()
        representation = storage.represent(resource_id)

        context = {
            'resource_id': resource_id,
            'representation': representation
        }
        return render(request, self.template_name, context)


class UsageView(StaffMemberRequiredMixin, generic.View):
    template_name = 'storage/usage.html'

    def get(self, request, resource_id):
        resource_id = parse_resource_id(resource_id)

        judgements = Judgement.objects.filter(
            Q(testcaseresult__input_resource_id=resource_id) |
            Q(testcaseresult__output_resource_id=resource_id) |
            Q(testcaseresult__answer_resource_id=resource_id) |
            Q(testcaseresult__stdout_resource_id=resource_id) |
            Q(testcaseresult__stderr_resource_id=resource_id)
        ).distinct()

        test_cases = TestCase.objects.filter(
            Q(input_resource_id=resource_id) |
            Q(answer_resource_id=resource_id)
        ).distinct()

        judgement_logs = JudgementLog.objects.filter(resource_id=resource_id)

        challenges = Challenge.objects.filter(
            Q(input_resource_id=resource_id) |
            Q(challengedsolution__output_resource_id=resource_id) |
            Q(challengedsolution__stdout_resource_id=resource_id) |
            Q(challengedsolution__stderr_resource_id=resource_id)
        ).distinct()

        files = FileMetadata.objects.filter(resource_id=resource_id)

        data_files = ProblemRelatedFile.objects.filter(resource_id=resource_id)
        source_files = ProblemRelatedSourceFile.objects.filter(resource_id=resource_id)

        context = {
            'resource_id': resource_id,
            'judgements': judgements,
            'test_cases': test_cases,
            'judgement_logs': judgement_logs,
            'challenges': challenges,
            'files': files,
            'data_files': data_files,
            'source_files': source_files,
        }
        return render(request, self.template_name, context)


class CleanupView(StaffMemberRequiredMixin, generic.View):
    def post(self, request, resource_id):
        resource_id = parse_resource_id(resource_id)
        rows_updated = 0
        rows_updated += TestCaseResult.objects.filter(stdout_resource_id=resource_id).update(stdout_resource_id=None)
        rows_updated += TestCaseResult.objects.filter(stderr_resource_id=resource_id).update(stderr_resource_id=None)
        msg = ungettext('%(rows)s DB row updated', '%(rows)s DB rows updated', rows_updated) % {'rows': rows_updated}
        messages.add_message(request, messages.INFO, msg)
        return redirect('storage:usage', resource_id)


class StatisticsView(StaffMemberRequiredMixin, generic.View):
    template_name = 'storage/statistics.html'

    def get(self, request):
        storage = create_storage()
        data = list(storage.list_all())

        context = {
            'total_size': sum(p[1] for p in data),
            'total_count': len(data),
            'top_list': sorted(data, key=lambda p: p[1], reverse=True)[:100]
        }
        return render(request, self.template_name, context)


class DownloadView(StaffMemberRequiredMixin, generic.View):
    def get(self, request, resource_id):
        resource_id = parse_resource_id(resource_id)
        return serve_resource(request, resource_id, content_type='application/octet-stream', force_download=True)


class IndexView(StaffMemberRequiredMixin, generic.TemplateView):
    template_name = 'storage/index.html'
