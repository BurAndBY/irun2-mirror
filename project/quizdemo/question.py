# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import namedtuple

Choice = namedtuple('Choice', 'text is_correct')


class Question(object):
    def __init__(self):
        self.text = ''


class MultiChoiceQuestion(Question):
    def __init__(self):
        super(MultiChoiceQuestion, self).__init__()
        self.choices = []

    def get_numbered_choices(self):
        for i, tpl in enumerate(self.choices):
            text, _ = tpl
            yield (i, text)

    def add_choice(self, text, is_correct=False):
        self.choices.append(Choice(text, is_correct))


class SingleAnswerQuestion(MultiChoiceQuestion):
    def get_answer_number(self):
        for i, choice in enumerate(self.choices):
            if choice.is_correct:
                return i


class MultipleAnswersQuestion(MultiChoiceQuestion):
    def get_answer_numbers(self):
        return [i for i, choice in enumerate(self.choices) if choice.is_correct]


class TextAnswerQuestion(Question):
    def __init__(self):
        super(TextAnswerQuestion, self).__init__()
        self._answer = ''

    def set_answer(self, text):
        self._answer = text

    def get_answer(self):
        return self._answer
