from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict

from .db import Session
from .security import decode_access_token
from .services import AccountingService
from .settings import settings

app = FastAPI()


def get_db_session():
    """Dependency that provides DB session."""
    with Session() as session:
        yield session


def get_accounting_service(
    session: Annotated[Session, Depends(get_db_session)],
):
    return AccountingService(session)


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


class RunningBillingCycleResponseData(BaseModel):
    credit: Decimal
    debit: Decimal

    model_config = ConfigDict(from_attributes=True)


@app.get(
    "/billing-cycles/running",
    dependencies=[Depends(RolesRequired(["manager", "accountant"]))],
    response_model=RunningBillingCycleResponseData,
)
def get_running_billing_cycle(
    accounting_service: Annotated[AccountingService, Depends(get_accounting_service)],
):
    return accounting_service.get_running_billing_cycle()


class ClosedBillingCycleResponseData(BaseModel):
    closed_at: datetime
    credit: Decimal
    debit: Decimal

    model_config = ConfigDict(from_attributes=True)


@app.get(
    "/billing-cycles/closed",
    dependencies=[Depends(RolesRequired(["manager", "accountant"]))],
    response_model=List[ClosedBillingCycleResponseData],
)
def get_closed_billing_cycles(
    accounting_service: Annotated[AccountingService, Depends(get_accounting_service)],
):
    return accounting_service.get_closed_billing_cycles()


class AuditLogRecordResponseData(BaseModel):
    credit: str
    debit: str
    created_at: datetime
    metadata: Any

    model_config = ConfigDict(from_attributes=True)


class AccountResponseData(BaseModel):
    balance: str
    audit_log_records: List[AuditLogRecordResponseData]

    model_config = ConfigDict(from_attributes=True)


@app.get(
    "/account",
    dependencies=[Depends(get_token_data)],
    response_model=AccountResponseData,
)
def get_account(
    token_data: Annotated[dict, Depends(get_token_data)],
    accounting_service: Annotated[AccountingService, Depends(get_accounting_service)],
):
    account = accounting_service.get_account(token_data["sub"])
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account
