from django.db import models


class Job(models.Model):
    ENQUEUED = 0
    PROCESSING = 1
    DONE = 2

    STATUS_CHOICES = (
        (ENQUEUED, 'Enqueued'),
        (PROCESSING, 'Processing'),
        (DONE, 'Done'),
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=ENQUEUED)
    stage = models.IntegerField(default=0)
    on_stage_progress = models.IntegerField(default=0)
    on_stage_max = models.IntegerField(default=0)

    x = models.IntegerField()
