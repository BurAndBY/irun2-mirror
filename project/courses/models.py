from django.db import models

from collections import namedtuple

from problems.models import ProblemFolder
from proglangs.models import Compiler


class Criterion(models.Model):
    label = models.CharField(max_length=8)
    name = models.CharField(max_length=64)


class Course(models.Model):
    name = models.CharField(max_length=64)
    compilers = models.ManyToManyField(Compiler, blank=True)


class Topic(models.Model):
    name = models.CharField(max_length=64)
    course = models.ForeignKey(Course, null=False, on_delete=models.CASCADE)
    problem_folder = models.ForeignKey(ProblemFolder, null=True, on_delete=models.SET_NULL)
    criteria = models.ManyToManyField(Criterion, blank=True)


class Slot(models.Model):
    topic = models.ForeignKey(Topic, null=False, on_delete=models.CASCADE)
