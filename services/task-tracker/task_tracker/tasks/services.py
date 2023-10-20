import re
from typing import Optional, Tuple

from django.core.exceptions import PermissionDenied
from django.db import transaction, models

from task_tracker.users.models import User
from .models import Task


JIRA_ID_RE = re.compile(r"\[(\w+-\d+)\]")

def split_title_jira_id(title: str) -> Tuple[str, str]:
    """Returns a 2-tuple: title without jira-id, jira-id."""
    jira_id_match = JIRA_ID_RE.search(title)
    if not jira_id_match:
        return title, ""
    jira_id = jira_id_match.group(1)
    title = title[:jira_id_match.start()] + title[jira_id_match.end():]
    return title, jira_id


class NoWorkers(Exception):
    """Raised when there are no active 'worker' users to assign a Task to."""


@transaction.atomic
def task_create(
    title: str,
    description: Optional[str] = None,
) -> Task:
    """Creates a new Task.

    Returns:
        Created Task object.

    Raises:
        NoWorkers: There are no active 'worker' users to assign new Task to.
    """
    title, jira_id = split_title_jira_id(title)
    task = Task(
        title=title,
        jira_id=jira_id,
        description=description,
    )

    assignee = User.objects.filter(role="worker", is_deleted=False).order_by("?").first()
    if not assignee:
        raise NoWorkers
    task.assignee = assignee

    task.full_clean()
    task.save()
    # TODO: send event
    return task


# TODO: add to event storming or delete with updated_at
@transaction.atomic
def task_update(
    task: Task,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> Task:
    update_fields = ["updated_at"]
    if title is not None:
        title, jira_id = split_title_jira_id(title)
        task.title = title
        task.jira_id = task.jira_id or new_jira_id
        update_fields.extend(["title", "jira_id"])

    if description is not None:
        task.description = description
        update_fields.append("description")

    task.save(update_fields=update_fields)
    # TODO: send event
    return task


@transaction.atomic
def task_complete(user: User, task: Task) -> Task:
    if task.user_id != user.pk and user.role not in ("admin", "accountant"):
        # TODO: add human readable message
        raise PermissionDenied

    task.status = Task.Status.COMPLETED
    task.save(update_fields=["status", "updated_at"])
    # TODO: send event
    return task


class NotEnoughWorkers(Exception):
    """Raised when there are not enough 'worker' users to reshuffle Tasks."""


@transaction.atomic
def task_reshuffle(user: User) -> int:
    """Reassigns all assigned tasks to random worker users. Returns number of reassigned tasks.

    Returns:
        Number of reshuffled Tasks.

    Raises:
        NotEnoughWorkers: There are not enough 'worker' users to reshuffle Tasks.
    """
    if user.role not in ("admin", "accountant"):
        # TODO: add human readable message
        raise PermissionDenied

    # at least 2 workers are necessary to guarantee that tasks can be reassigned
    if User.objects.filter(role="worker").count() < 2:
        raise NotEnoughWorkers

    tasks = list(Task.objects.reshuffle())
    # TODO: send events
    return len(tasks)
