import datetime
from decimal import Decimal
from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select

from .db import Session
from .models import Account, NewTaskAddedEvent, TaskCompletedEvent, TaskReassignedEvent
from .security import decode_access_token
from .settings import settings

app = FastAPI()


def get_db_session():
    """Dependency that provides DB session."""
    with Session() as session:
        yield session


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


class StatsResponseData(BaseModel):
    earnings: Decimal
    debtors: int


@app.get("/stats", dependencies=[Depends(RolesRequired(["manager"]))])
def get_stats(session: Annotated[Session, Depends(get_db_session)]):
    date = datetime.datetime.utcnow().date()
    new_tasks_earnings = session.scalars(
        select(func.coalesce(func.sum(NewTaskAddedEvent.assignment_price), 0)).where(
            cast(NewTaskAddedEvent.timestamp, Date) == date
        )
    ).one()
    reassigned_tasks_earnings = session.scalars(
        select(func.coalesce(func.sum(TaskReassignedEvent.assignment_price), 0)).where(
            cast(TaskReassignedEvent.timestamp, Date) == date
        )
    ).one()
    completed_tasks_payments = session.scalars(
        select(func.coalesce(func.sum(TaskCompletedEvent.completion_price), 0)).where(
            cast(TaskCompletedEvent.timestamp, Date) == date
        )
    ).one()
    earnings = new_tasks_earnings + reassigned_tasks_earnings - completed_tasks_payments

    debtors = session.scalars(
        select(func.count(Account.public_id)).where(Account.balance < 0)
    ).one()

    return StatsResponseData(earnings=earnings, debtors=debtors)


class DailyTaskStatsResponseData(BaseModel):
    max_price: Decimal
    date: datetime.date


@app.get(
    "/task-stats",
    dependencies=[Depends(RolesRequired(["manager"]))],
    response_model=List[DailyTaskStatsResponseData],
)
def get_task_stats(session: Annotated[Session, Depends(get_db_session)]):
    return session.execute(
        select(
            func.max(TaskCompletedEvent.completion_price).label("max_price"),
            cast(TaskCompletedEvent.timestamp, Date).label("date"),
        )
        .group_by(cast(TaskCompletedEvent.timestamp, Date))
        .order_by(cast(TaskCompletedEvent.timestamp, Date))
    ).all()
