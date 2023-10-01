import uuid

from django.db import models
from django.utils import timezone


class EventQuerySet(models.QuerySet):
    def unsent(self):
        """Returns a QuerySet of unsent events only."""
        return self.filter(sent_at__isnull=True)


class Event(models.Model):
    objects = models.Manager.from_queryset(EventQuerySet)()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    version = models.PositiveSmallIntegerField()
    key = models.CharField(max_length=255)
    data = models.JSONField()
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "event"

    def mark_sent(self):
        """Sets `self.sent_at` to current time."""
        if self.sent_at is not None:
            self.sent_at = timezone.now()

    @property
    def payload(self):
        return {
            "event_name": self.name,
            "event_version": self.version,
            "data": self.data,
        }
