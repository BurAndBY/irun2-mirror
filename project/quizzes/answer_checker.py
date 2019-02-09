from .models import Question

from collections import namedtuple


AnswersInfo = namedtuple('AnswersInfo', 'chosen_correct chosen_incorrect total_correct')


class Policy(object):
    STRICT = 0
    SOFT = 1


class IAnswerChecker(object):
    def get_result_points(self, question, policy=Policy.STRICT):
        raise NotImplementedError()


class SingleAnswerChecker(IAnswerChecker):
    key = Question.SINGLE_ANSWER

    def get_result_points(self, question, policy=Policy.STRICT):
        is_right = False
        for answer in question.sessionquestionanswer_set.select_related('choice').all():
            if answer.is_chosen and answer.choice.is_right:
                is_right = True
                break
        if is_right:
            return question.points
        return 0.


class TextAnswerChecker(IAnswerChecker):
    key = Question.TEXT_ANSWER

    def get_result_points(self, question, policy=Policy.STRICT):
        answer = question.sessionquestionanswer_set.select_related('choice').first()
        if answer and answer.user_answer and answer.user_answer.strip() == answer.choice.text:
            return question.points
        return 0.


class MultipleAnswersChecker(IAnswerChecker):
    key = Question.MULTIPLE_ANSWERS

    def get_result_points(self, question, policy=Policy.STRICT):
        chosen_correct = 0    # chosen and right
        chosen_incorrect = 0  # chosen but not right
        total_correct = 0     # right choice
        for answer in question.sessionquestionanswer_set.select_related('choice').all():
            if answer.choice.is_right:
                total_correct += 1
            if answer.is_chosen and answer.choice.is_right:
                chosen_correct += 1
            elif answer.is_chosen:
                chosen_incorrect += 1
        return question.points * _get_points_with_policy(AnswersInfo(chosen_correct, chosen_incorrect, total_correct),
                                                         policy)


def _get_points_with_policy(answers, policy):
    handler = _POLICIES[policy]
    if not handler:
        raise NotImplementedError()
    return handler.estimate(answers)


class IPolicy(object):
    def estimate(self, answers):
        raise NotImplementedError()


class StrictPolicy(IPolicy):
    key = Policy.STRICT

    def estimate(self, answers):
        if answers.chosen_incorrect == 0 and answers.chosen_correct == answers.total_correct:
            return 1.
        return 0.


class SoftPolicy(IPolicy): # author: Artur Mialikov
    key = Policy.SOFT

    def heaviside(self, score):
        return 0. if score < 0 else 1 

    def estimate(self, answers):
        r = answers.chosen_correct
        w = answers.chosen_incorrect
        k = answers.total_correct
        return self.heaviside(r - w) * (r - w) / max(r + w, k)


_POLICIES = {
    Policy.STRICT: StrictPolicy(),
    Policy.SOFT: SoftPolicy()
}


CHECKERS = {
    Question.SINGLE_ANSWER: SingleAnswerChecker(),
    Question.MULTIPLE_ANSWERS: MultipleAnswersChecker(),
    Question.TEXT_ANSWER: TextAnswerChecker()
}
