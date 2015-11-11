class Enum(type):
    def parse(cls, value):
        for code, literal, _ in cls.VALUES:
            if literal == value:
                return code
        raise ValueError('Unable to parse \'{0}\' as {1} value'.format(value, cls.__name__))

    def text(cls, value):
        for code, _, text in cls.VALUES:
            if code == value:
                return text
        raise ValueError('Unable to get text')

    def literal(cls, value):
        for code, literal, _ in cls.VALUES:
            if code == value:
                return literal
        raise ValueError('Unable to get text')

    def __getattr__(cls, name):
        for code, literal, _ in cls.VALUES:
            if literal == name:
                return code
        raise AttributeError('type object \'{0}\' has no attribute \'{1}\''.format(cls.__name__, name))


class JudgementStatusEnum:
    __metaclass__ = Enum
    VALUES = (
        (0, 'ENQUEUED', 'Waiting'),
        (1, 'DONE', 'Done'),
        (2, 'PREPARING', 'Preparing to test'),
        (3, 'COMPILING', 'Compiling'),
        (4, 'TESTING', 'Testing'),
        (5, 'UPLOADING', 'Uploading results'),
    )


class OutcomeEnum:
    __metaclass__ = Enum
    VALUES = (
        (0, 'ACCEPTED', 'Accepted'),
        (1, 'TIME_LIMIT_EXCEEDED', 'Time Limit Exceeded'),
        (2, 'MEMORY_LIMIT_EXCEEDED', 'Memory Limit Exceeded'),
        (3, 'IDLENESS_LIMIT_EXCEEDED', 'Idleness Limit Exceeded'),
        (4, 'RUNTIME_ERROR', 'Runtime Error'),
        (5, 'SECURITY_VIOLATION', 'Security Violation'),
        (6, 'WRONG_ANSWER', 'Wrong Answer'),
        (7, 'PRESENTATION_ERROR', 'Presentation Error'),
        (8, 'CHECK_FAILED', 'Check Failed'),
    )
