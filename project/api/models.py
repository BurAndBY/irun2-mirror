from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models import Validation
from solutions.models import Judgement, ChallengedSolution


class DbObjectInQueue(models.Model):
    WAITING = 0
    EXECUTING = 1
    DONE = 2

    STATE_CHOICES = (
        (WAITING, _('Waiting')),
        (EXECUTING, _('Executing')),
        (DONE, _('Done')),
    )

    worker = models.CharField(max_length=64, blank=True)
    state = models.IntegerField(default=WAITING, choices=STATE_CHOICES)

    creation_time = models.DateTimeField()
    last_update_time = models.DateTimeField()

    priority = models.IntegerField()

    judgement = models.ForeignKey(Judgement, null=True, on_delete=models.CASCADE)
    validation = models.ForeignKey(Validation, null=True, on_delete=models.CASCADE)
    challenged_solution = models.ForeignKey(ChallengedSolution, null=True, on_delete=models.CASCADE)
