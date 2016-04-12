from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from solutions.models import Solution

class Algorithm(models.Model):
    id = models.IntegerField(verbose_name='ID', primary_key=True)
    name = models.CharField(max_length=255)
    enabled = models.BooleanField()

class JudgementResult(models.Model):
    solution_to_judge = models.ForeignKey(Solution),
    solution_to_compare = models.ForeignKey(Solution),
    algo_id = models.ForeignKey(Algorithm),
    similarity = models.FloatField()
    verdict = models.CharField(max_length=2048)

class AggregatedResult(models.Model):
    id = models.ForeignKey(Solution, primary_key=True)
    relevance = models.FloatField()

