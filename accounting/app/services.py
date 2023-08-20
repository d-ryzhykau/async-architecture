from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from .db import Session
from .models import Account, AuditLogRecord, BillingCycle


class AccountingService:
    def __init__(self, session: Session):
        self.session = session

    def get_running_billing_cycle(self):
        query = select(
            func.coalesce(func.sum(AuditLogRecord.credit), 0).label("credit"),
            func.coalesce(func.sum(AuditLogRecord.debit), 0).label("debit"),
        ).filter(
            AuditLogRecord.billing_cycle_id == None  # noqa: E711
        )
        billing_cycle_data = self.session.execute(query).one()
        return {"credit": billing_cycle_data.credit, "debit": billing_cycle_data.debit}

    def get_closed_billing_cycles(self):
        query = select(BillingCycle)
        return self.session.scalars(query).all()

    def get_account(self, user_public_id: str):
        query = (
            select(Account)
            .filter_by(owner_public_id=user_public_id)
            .options(joinedload(Account.audit_log_records))
        )
        return self.session.scalars(query).one_or_none()

    def credit_for_task_completion(self, task_public_id: str):
        ...

    def debit_for_new_task(self, new_task_data: dict):
        ...

    def debit_for_task_assignment(self, task_public_id: str):
        ...
