from typing import Annotated, List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from .db import Session
from .security import decode_access_token
from .services import (
    NoWorkerUsers,
    TaskAlreadyCompleted,
    TaskNotAssignedToUser,
    TaskNotFound,
    TaskService,
)
from .settings import settings

app = FastAPI()


def get_db_session():
    """Dependency that provides DB session."""
    with Session() as session:
        yield session


def get_task_service(
    session: Annotated[Session, Depends(get_db_session)],
):
    return TaskService(session)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=str(settings.auth_token_url))


def get_token_data(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Dependency that verifies access token and returns its data."""
    token_data = decode_access_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


class RolesRequired:
    """Dependency that checks if the role in the access token matches."""

    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def __call__(self, token_data: Annotated[dict, Depends(get_token_data)]):
        if token_data.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )


class TaskDataResponse(BaseModel):
    id: int
    public_id: UUID4
    is_completed: bool
    description: str
    jira_id: Optional[str]
    assigned_to_public_id: UUID4

    model_config = ConfigDict(from_attributes=True)


@app.get(
    "/tasks/",
    dependencies=[Depends(get_token_data)],
    response_model=List[TaskDataResponse],
)
def get_tasks(
    token_data: Annotated[dict, Depends(get_token_data)],
    assigned_to: Optional[Literal["me"]] = None,
    task_service: TaskService = Depends(get_task_service),
):
    if assigned_to == "me":
        return task_service.get_tasks(assigned_to_public_id=token_data["sub"])
    return task_service.get_tasks()


class CreateTaskRequest(BaseModel):
    description: str


@app.post(
    "/tasks/",
    dependencies=[Depends(get_token_data)],
    status_code=status.HTTP_201_CREATED,
    response_model=TaskDataResponse,
)
def create_task(
    payload: CreateTaskRequest,
    task_service: Annotated[TaskService, Depends(get_task_service)],
):
    try:
        return task_service.create_task(payload.description)
    except NoWorkerUsers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No worker Users",
        )


# TODO: add support for description update with sync to other services
class UpdateTaskRequest(BaseModel):
    is_completed: bool

    @field_validator("is_completed")
    @classmethod
    def is_completed_is_true(cls, v: bool):
        if not v:
            raise ValueError("is_completed cannot be false")
        return v


# TODO: consider using public_id in routes
@app.patch(
    "/tasks/{task_id}",
    response_model=TaskDataResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Task can be marked as completed only by assigned User",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Task with given UUID was not found",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Task has already been completed",
        },
    },
)
def update_task(
    task_id: int,
    payload: UpdateTaskRequest,
    token_data: Annotated[dict, Depends(get_token_data)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
):
    try:
        return task_service.complete_task(
            user_public_id=token_data["sub"],
            task_id=task_id,
        )
    except TaskNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )
    except TaskNotAssignedToUser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task is assigned to another User",
        )
    except TaskAlreadyCompleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task has already been completed",
        )


@app.post(
    "/tasks/reassign",
    dependencies=[Depends(RolesRequired("manager"))],
    response_model=List[TaskDataResponse],
)
def reassign_tasks(
    task_service: Annotated[TaskService, Depends(get_task_service)],
):
    try:
        return task_service.reassign_open_tasks()
    except NoWorkerUsers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No worker Users",
        )
