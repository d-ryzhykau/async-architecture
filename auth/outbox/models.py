import uuid

from django.db import models


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    version = models.PositiveSmallIntegerField()
    key = models.CharField(max_length=255)
    data = models.JSONField()
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "event"
