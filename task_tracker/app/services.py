from typing import List, Optional

from sqlalchemy import select, text, update

from .db import Session
from .event_producer import (
    NewTaskAdded,
    TaskCompleted,
    TaskCreated,
    TaskReassigned,
    send_events,
)
from .models import Task, User


class TaskNotFound(Exception):
    """Raised when a Task was not found."""


class TaskNotAssignedToUser(Exception):
    """Raised on an attempt to complete Task by an unassigned User."""


class TaskAlreadyCompleted(Exception):
    """Raised on an attempt to complete an already completed Task."""


class TaskService:
    def __init__(self, session: Session):
        self.session = session

    def get_tasks(self, assigned_to_public_id: Optional[str] = None) -> List[Task]:
        query = select(Task)
        if assigned_to_public_id:
            query = query.filter_by(assigned_to_public_id=assigned_to_public_id)
        return self.session.scalars(query).all()

    def _get_random_worker_subquery(self):
        return (
            select(User.public_id)
            .filter_by(role="worker")
            .order_by(text("RANDOM()"))
            .limit(1)
            .scalar_subquery()
        )

    def create_task(self, description: str):
        task = Task(
            description=description,
            assigned_to_public_id=self._get_random_worker_subquery(),
        )
        with self.session.begin():
            self.session.add(task)
            self.session.flush()

            send_events([TaskCreated.from_task(task), NewTaskAdded.from_task(task)])

        return task

    def complete_task(self, user_public_id: str, task_id: int) -> Task:
        query = select(Task).filter_by(id=task_id).with_for_update()
        with self.session.begin():
            task = self.session.scalars(query).one_or_none()
            if task is None:
                raise TaskNotFound
            if task.assigned_to_public_id != user_public_id:
                raise TaskNotAssignedToUser
            if task.is_completed:
                raise TaskAlreadyCompleted

            task.is_completed = True

            send_events([TaskCompleted.from_task(task)])

        return task

    def reassign_open_tasks(self) -> List[Task]:
        reassign_open_tasks_query = (
            update(Task)
            .filter_by(is_completed=False)
            .values(assigned_to_public_id=self._get_random_worker_subquery())
            .returning(Task)
        )
        with self.session.begin():
            reassigned_tasks = self.session.scalars(reassign_open_tasks_query)

            send_events([TaskReassigned.from_task(task) for task in reassigned_tasks])

        return reassigned_tasks
