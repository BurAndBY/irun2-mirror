from .models import Question


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
        return question.points * _get_points_with_policy(
            {"total_correct": total_correct, "chosen_correct": chosen_correct, "chosen_incorrect": chosen_incorrect},
            policy)


def _get_points_with_policy(answers, policy):
    if policy == Policy.STRICT:
        return _strict_policy_estimate(answers)
    elif policy == Policy.SOFT:
        return _soft_policy_estimate(answers)
    else:
        return 0.


def _strict_policy_estimate(answers):
    if answers['chosen_incorrect'] == 0 and answers['chosen_correct'] == answers['total_correct']:
        return 1.
    return 0.


def _soft_policy_estimate(answers):
    raise NotImplementedError()


CHECKERS = [
    SingleAnswerChecker(),
    MultipleAnswersChecker(),
    TextAnswerChecker()
]
