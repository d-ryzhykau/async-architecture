from typing import List, Optional

from sqlalchemy import select, text, update

from .db import Session
from .event_producer import send_events, NewTaskAdded, TaskAssigned, TaskCompleted
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

    def get_tasks(self, assigned_to_uuid: Optional[str]) -> List[Task]:
        query = select(Task)
        if assigned_to_uuid:
            query = query.filter_by(assigned_to_uuid=assigned_to_uuid)
        return self.session.scalars(query).all()

    def _get_random_worker_subquery(self):
        return (
            select(User.uuid)
            .filter_by(role="worker", is_deleted=False)
            .order_by(text("RANDOM()"))
            .limit(1)
            .scalar_subquery()
        )

    def create_task(self, description: str):
        task = Task(
            description=description,
            assigned_to_uuid=self._get_random_worker_subquery(),
        )
        with self.session.begin():
            self.session.add(task)
            self.session.flush()

            send_events([NewTaskAdded.from_task(task)])

        return task

    def complete_task(self, user_uuid: str, task_uuid: str) -> Task:
        query = select(Task).filter_by(uuid=task_uuid).with_for_update()
        with self.session.begin():
            task = self.session.scalars(query).one_or_none()
            if task is None:
                raise TaskNotFound
            if task.assigned_to_uuid != user_uuid:
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
            .values(assigned_to_uuid=self._get_random_worker_subquery())
            .returning(Task)
        )
        with self.session.begin():
            reassigned_tasks = self.session.scalars(reassign_open_tasks_query)

            send_events(
                [
                    TaskAssigned.from_task(task)
                    for task in reassigned_tasks
                ]
            )

        return reassigned_tasks
