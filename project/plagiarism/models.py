from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from solutions.models import Solution

class Algorithm(models.Model):
    name = models.CharField(max_length=255)
    enabled = models.BooleanField()

class JudgementResult(models.Model):
    solution_to_judge = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='solution_to_judge')
    solution_to_compare = models.ForeignKey(Solution, on_delete=models.CASCADE, related_name='solution_to_compare')
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)
    similarity = models.FloatField()
    verdict = models.CharField(max_length=2048)

class AggregatedResult(models.Model):
    id = models.OneToOneField(Solution, on_delete=models.CASCADE, primary_key=True)
    relevance = models.FloatField()
