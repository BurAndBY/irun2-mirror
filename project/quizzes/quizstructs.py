class QuizAnswer(object):
    def __init__(self, id, chosen, user_answer):
        self.id = id
        self.chosen = chosen
        self.user_answer = user_answer


class QuizAnswersData(object):
    def __init__(self, answers):
        self.answers = answers


class SaveAnswerMessage(object):
    def __init__(self, message):
        self.message = message
