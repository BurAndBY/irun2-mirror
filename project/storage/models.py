from django.db import models
from .storage import ResourceIdField


# Create your models here.
class AuditRecord(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    resource_id = ResourceIdField()
