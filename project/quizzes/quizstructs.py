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


class QuestionChoice(object):
    def __init__(self, id, is_right, text):
        self.id = id
        self.is_right = is_right
        self.text = text


class QuestionData(object):
    def __init__(self, id, text, type, choices):
        self.id = id
        self.text = text
        self.type = type
        self.choices = choices
