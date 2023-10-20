from django.apps import apps
from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskManager(models.Manager):
    def reshuffle(self) -> models.query.RawQuerySet:
        assignee_field = Task._meta.get_field("assignee")
        assignee_column = assignee_field.column
        assignee_to_table = assignee_field.related_model._meta.db_table
        assignee_to_column = assignee_field.foreign_related_fields[0].column

        status_column = Task._meta.get_field("status").column

        return Task.objects.raw(
            f"""
            UPDATE
                {Task._meta.db_table} AS t
            SET
                {assignee_column} = (
                    SELECT
                        {assignee_to_column}
                    FROM
                        {assignee_to_table}
                    WHERE
                        -- do not assign to current assignee
                        {assignee_to_column} != t.{assignee_column}
                        AND role = 'worker'
                        AND NOT is_deleted
                    ORDER BY
                        RANDOM()
                    LIMIT 1
                )
            WHERE
                {status_column} = %s
            RETURNING *
            """,
            [Task.Status.ASSIGNED],
        )


class Task(models.Model):
    objects = TaskManager()

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
