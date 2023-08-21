import re
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, text, update

from .db import Session
from .event_producer import (
    NewTaskAddedV1,
    TaskCompletedV1,
    TaskCreatedV1,
    TaskReassignedV1,
    send_events,
)
from .models import Task, User


class TaskNotFound(Exception):
    """Raised when a Task was not found."""


class TaskNotAssignedToUser(Exception):
    """Raised on an attempt to complete Task by an unassigned User."""


class TaskAlreadyCompleted(Exception):
    """Raised on an attempt to complete an already completed Task."""


class NoWorkerUsers(Exception):
    """Raised when there are no worker Users to be assigned to Task."""


# JIRA ID regex. Group 1 corresponds to text between square brackets:
# "[jira-123] spam" -> group 1 = "jira-123"
jira_id_re = re.compile(r"\[([\w\-]+)\]")


# TODO: rework to guarantee that kafka message is dispatched for each DB write
class TaskService:
    def __init__(self, session: Session):
        self.session = session

    def get_tasks(self, assigned_to_public_id: Optional[str] = None) -> List[Task]:
        query = select(Task)
        if assigned_to_public_id:
            query = query.filter_by(assigned_to_public_id=assigned_to_public_id)
        return self.session.scalars(query).all()

    def _get_worker_public_id_query(self):
        return (
            select(User.public_id)
            .filter_by(role="worker", is_deleted=False)
        )

    def _get_random_worker_public_id_subquery(self):
        return (
            self._get_worker_public_id_query()
            .order_by(text("RANDOM()"))
            .limit(1)
            .scalar_subquery()
        )

    def create_task(self, description: str):
        jira_id: Optional[str] = None

        jira_id_match = jira_id_re.search(description)
        if jira_id_match:
            jira_id = jira_id_match.group(1).strip()
            description = (
                description[:jira_id_match.start()]
                + description[jira_id_match.end():]
            )

        task = Task(
            description=description.strip(),
            jira_id=jira_id,
            assigned_to_public_id=self._get_random_worker_public_id_subquery(),
        )

        with self.session.begin():
            if not self.session.scalars(
                self._get_worker_public_id_query().exists().select()
            ).one():
                raise NoWorkerUsers

            self.session.add(task)
            self.session.flush()

            send_events([TaskCreatedV1.from_task(task), NewTaskAddedV1.from_task(task)])

        return task

    def complete_task(self, user_public_id: str, task_id: int) -> Task:
        query = select(Task).filter_by(id=task_id).with_for_update()
        with self.session.begin():
            task = self.session.scalars(query).one_or_none()
            if task is None:
                raise TaskNotFound
            if task.assigned_to_public_id != UUID(user_public_id):
                raise TaskNotAssignedToUser
            if task.is_completed:
                raise TaskAlreadyCompleted

            task.is_completed = True

            send_events([TaskCompletedV1.from_task(task)])

        return task

    def reassign_open_tasks(self) -> List[Task]:
        reassign_open_tasks_query = (
            update(Task)
            .filter_by(is_completed=False)
            .values(
                assigned_to_public_id=self._get_random_worker_public_id_subquery(),
            )
            .returning(Task)
        )
        with self.session.begin():
            if not self.session.scalars(
                self._get_worker_public_id_query().exists().select()
            ).one():
                raise NoWorkerUsers

            reassigned_tasks = self.session.scalars(reassign_open_tasks_query).all()

            send_events([TaskReassignedV1.from_task(task) for task in reassigned_tasks])

        return reassigned_tasks
