# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import smtplib

from django import forms
from django.core.mail import send_mail
from django.urls import reverse
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.encoding import force_text
from django.utils.translation import gettext, gettext_lazy
from django.views import generic

from .mixins import CoachMixin
from .models import (
    IcpcCoach,
    IcpcTeam,
    IcpcContestant,
    CONTESTANTS_PER_TEAM,
)
from .forms import (
    IcpcCoachForm,
    IcpcCoachUpdateForm,
    IcpcTeamForm,
    IcpcContestantForm,
)
from events.mixins import EventMixin


def _create_coach_dashboard_link(request, event, coach):
    url = reverse('events:list_teams', kwargs={
        'slug': event.slug,
        'coach_id': coach.human_readable_id,
    })
    return request.build_absolute_uri(url)


LETTER = gettext_lazy('''%(full_name)s,

You have been registered as a coach. To edit your team data, use the following link:
%(link)s

--
iRunner 2
''')


def _send_link_to_email(event, coach, link):
    subject = '{}: {}'.format(force_text(gettext('Registration')), event.name)
    message = force_text(LETTER) % {
        'full_name': coach.full_name,
        'link': link,
    }
    send_mail(subject, message, None, [coach.email])


class RegisterCoachView(EventMixin, generic.CreateView):
    model = IcpcCoach
    form_class = IcpcCoachForm
    template_name = 'registration/new_coach.html'
    result_template_name = 'registration/new_coach_result.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'instance': self.model(event=self.event)
        })
        return kwargs

    def form_valid(self, form):
        coach = form.save()
        self.object = coach
        link = _create_coach_dashboard_link(self.request, self.event, coach)

        sent = False
        try:
            _send_link_to_email(self.event, coach, link)
            sent = True
        except smtplib.SMTPException:
            logging.exception('Unable to send e-mail')
            coach.delete()
        except Exception:
            coach.delete()
            raise

        context = self.get_context_data(sent=sent, email=coach.email)
        return render(self.request, self.result_template_name, context)


class UpdateCoachView(EventMixin, CoachMixin, generic.UpdateView):
    form_class = IcpcCoachUpdateForm
    template_name = 'registration/update_coach.html'

    def get_object(self):
        return self.coach

    def get_success_url(self):
        return reverse('events:list_teams', kwargs={'slug': self.event.slug, 'coach_id': self.coach_id_str})


class ListTeamsView(EventMixin, CoachMixin, generic.TemplateView):
    template_name = 'registration/teams.html'

    def get_context_data(self, **kwargs):
        context = super(ListTeamsView, self).get_context_data(**kwargs)
        team_participants = {}
        for team_id, last_name in IcpcContestant.objects.order_by('id').values_list('team_id', 'last_name'):
            team_participants.setdefault(team_id, []).append(last_name)

        teams = []
        for team in self.coach.icpcteam_set.order_by('id').all():
            team.participants = ', '.join(filter(None, team_participants.get(team.id, [])))
            teams.append(team)
        context['teams'] = teams
        return context


def _make_forms(data, instance=None):
    team_form = IcpcTeamForm(data=data, instance=instance)
    if instance is None:
        qs = IcpcContestant.objects.none()
    else:
        qs = IcpcContestant.objects.filter(team=instance).order_by('id')

    FormSet = forms.modelformset_factory(IcpcContestant, form=IcpcContestantForm,
                                         min_num=CONTESTANTS_PER_TEAM, validate_min=True,
                                         max_num=CONTESTANTS_PER_TEAM, validate_max=True,
                                         extra=max(CONTESTANTS_PER_TEAM - len(qs), 0))
    contestant_formset = FormSet(data=data, queryset=qs)
    return team_form, contestant_formset


class CreateTeamView(EventMixin, CoachMixin, generic.base.ContextMixin, generic.View):
    template_name = 'registration/team.html'

    def get(self, request, *args, **kwargs):
        team_form, contestant_formset = _make_forms(None)
        context = self.get_context_data(team_form=team_form, contestant_formset=contestant_formset)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        team_form, contestant_formset = _make_forms(request.POST)
        if team_form.is_valid() and contestant_formset.is_valid():
            with transaction.atomic():
                team = team_form.save(commit=False)
                team.coach = self.coach
                team.save()
                contestant_formset.save(commit=False)
                for contestant in contestant_formset.new_objects:
                    contestant.team = team
                    contestant.save()
            return redirect('events:list_teams', self.event.slug, self.coach_id_str)

        context = self.get_context_data(team_form=team_form, contestant_formset=contestant_formset)
        return render(request, self.template_name, context)


class UpdateTeamView(EventMixin, CoachMixin, generic.base.ContextMixin, generic.View):
    template_name = 'registration/team.html'

    def _get_team(self, team_id):
        return get_object_or_404(IcpcTeam, pk=team_id, coach=self.coach)

    def get(self, request, slug, coach_id, team_id):
        team = self._get_team(team_id)
        team_form, contestant_formset = _make_forms(None, team)
        context = self.get_context_data(team_form=team_form, contestant_formset=contestant_formset)
        return render(request, self.template_name, context)

    def post(self, request, slug, coach_id, team_id):
        team = self._get_team(team_id)
        team_form, contestant_formset = _make_forms(request.POST, team)
        if team_form.is_valid() and contestant_formset.is_valid():
            with transaction.atomic():
                team.save()
                contestant_formset.save()
            return redirect('events:list_teams', self.event.slug, self.coach_id_str)

        context = self.get_context_data(team_form=team_form, contestant_formset=contestant_formset)
        return render(request, self.template_name, context)
