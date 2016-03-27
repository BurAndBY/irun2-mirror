from django.utils.translation import ugettext_lazy as _


class Outcome(object):
    NOT_AVAILABLE = 0
    ACCEPTED = 1
    COMPILATION_ERROR = 2
    WRONG_ANSWER = 3
    TIME_LIMIT_EXCEEDED = 4
    MEMORY_LIMIT_EXCEEDED = 5
    IDLENESS_LIMIT_EXCEEDED = 6
    RUNTIME_ERROR = 7
    PRESENTATION_ERROR = 8
    SECURITY_VIOLATION = 9
    CHECK_FAILED = 10

    CHOICES = (
        (NOT_AVAILABLE, _('N/A')),
        (ACCEPTED, _('Accepted')),
        (COMPILATION_ERROR, _('Compilation Error')),
        (WRONG_ANSWER, _('Wrong Answer')),
        (TIME_LIMIT_EXCEEDED, _('Time Limit Exceeded')),
        (MEMORY_LIMIT_EXCEEDED, _('Memory Limit Exceeded')),
        (IDLENESS_LIMIT_EXCEEDED, _('Idleness Limit Exceeded')),
        (RUNTIME_ERROR, _('Run-time Error')),
        (PRESENTATION_ERROR, _('Presentation Error')),
        (SECURITY_VIOLATION, _('Security Violation')),
        (CHECK_FAILED, _('Check Failed'))
    )
