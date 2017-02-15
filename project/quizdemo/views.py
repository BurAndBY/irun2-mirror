from __future__ import unicode_literals

import random
import sys

from django import forms
from django.shortcuts import render, redirect
from django.views.generic import View

from cauth.mixins import LoginRequiredMixin
from common.katex import tex2html

from quizdemo.factory import FACTORIES
from quizdemo.question import MultiChoiceQuestion, SingleAnswerQuestion, MultipleAnswersQuestion, TextAnswerQuestion


def get_seed():
    return random.randint(0, sys.maxint)


def get_factory(slug):
    for factory in FACTORIES:
        if factory.slug == slug:
            return factory


class IndexView(LoginRequiredMixin, View):
    template_name = 'quizdemo/index.html'

    def get(self, request):
        context = {
            'factories': FACTORIES,
            'seed': get_seed()
        }
        return render(request, self.template_name, context)


def make_form(question):
    if isinstance(question, MultiChoiceQuestion):
        choices = [
            (i, tex2html(text)) for i, text in question.get_numbered_choices()
        ]

        if isinstance(question, SingleAnswerQuestion):
            class Form(forms.Form):
                ans = forms.TypedChoiceField(choices=choices, coerce=int, widget=forms.RadioSelect)
            return Form(initial={'ans': question.get_answer_number()})

        if isinstance(question, MultipleAnswersQuestion):
            class Form(forms.Form):
                ans = forms.TypedMultipleChoiceField(choices=choices, coerce=int, widget=forms.CheckboxSelectMultiple)
            return Form(initial={'ans': question.get_answer_numbers()})

    if isinstance(question, TextAnswerQuestion):
        class Form(forms.Form):
            ans = forms.CharField()
        return Form(initial={'ans': question.get_answer()})


class QuestionView(LoginRequiredMixin, View):
    template_name = 'quizdemo/question.html'

    def get(self, request, slug, seed):
        factory = get_factory(slug)
        if factory is None:
            return redirect('quizdemo:index')

        rng = random.Random(int(seed))
        q = factory.make_question(rng)

        context = {
            'slug': slug,
            'text': tex2html(q.text),
            'form': make_form(q),
            'seed': get_seed()
        }
        return render(request, self.template_name, context)
