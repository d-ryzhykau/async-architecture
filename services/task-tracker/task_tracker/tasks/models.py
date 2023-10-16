from django.db import models
from django.utils.translation import gettext_lazy as _


class Task(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", _("Assigned")
        COMPLETED = "completed", _("Completed")

    public_id = models.UUIDField(unique=True)

    title = models.CharField(max_length=128)
    jira_id = models.CharField(max_length=24, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ASSIGNED,
    )
    assignee = models.ForeignKey(
        "users.User",
        related_name="tasks",
        on_delete=models.RESTRICT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "task"
