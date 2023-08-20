from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
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

    def create_account(self, user_public_id: str):
        query = (
            insert(Account)
            .values(balance=0, owner_public_id=user_public_id)
            .on_conflict_do_nothing()
            .returning(Account)
        )
        return self.session.scalars(query).one()

    # TODO: split into 2 services: new task handler and task reassigned handler
    def debit_for_task_assignment(
        self,
        task_public_id: str,
        assigned_to_public_id: str,
        assignment_price: str,
    ):
        assignment_price = Decimal(assignment_price)

        with self.session.begin():
            account_id = self.session.scalars(
                insert(Account)
                .values(
                    owner_public_id=assigned_to_public_id,
                    balance=-assignment_price,
                )
                .on_conflict_do_update(
                    Account.owner_public_id,
                    set_={Account.balance: Account.balance - assignment_price},
                )
                .returning(Account.id)
            ).one()

            audit_log_record = AuditLogRecord(
                debit=assignment_price,
                account_id=account_id,
                info={
                    "reason": "task_assigned",
                    "task_public_id": task_public_id,
                },
            )
            self.session.add(audit_log_record)

            self.session.flush()

    def credit_for_task_completion(
        self,
        task_public_id: str,
        assigned_to_public_id: str,
        completion_price: str,
    ):
        completion_price = Decimal(completion_price)

        with self.session.begin():
            account_id = self.session.scalars(
                insert(Account)
                .values(
                    owner_public_id=assigned_to_public_id,
                    balance=completion_price,
                )
                .on_conflict_do_update(
                    Account.owner_public_id,
                    set_={Account.balance: Account.balance + completion_price},
                )
                .returning(Account.id)
            ).one()

            audit_log_record = AuditLogRecord(
                credit=completion_price,
                account_id=account_id,
                info={
                    "reason": "task_completed",
                    "task_public_id": task_public_id,
                },
            )
            self.session.add(audit_log_record)

            self.session.flush()

    def close_billing_cycle(self):
        # TODO: call in cron
        billing_cycle_credit_subquery = (
            select(
                func.coalesce(func.sum(AuditLogRecord.credit), 0)
            )
            .filter(AuditLogRecord.billing_cycle_id == None)  # noqa: E711
            .subquery()
        )
        billing_cycle_debit_subquery = (
            select(
                func.coalesce(func.sum(AuditLogRecord.debit), 0)
            )
            .filter(AuditLogRecord.billing_cycle_id == None)  # noqa: E711
            .subquery()
        )
        with self.session.begin():
            billing_cycle_id = self.session.scalars(
                insert(BillingCycle)
                .values(
                    credit=billing_cycle_credit_subquery,
                    debit=billing_cycle_debit_subquery,
                )
                .returning(BillingCycle.id)
            ).one()

            self.session.execute(
                update(AuditLogRecord)
                .filter(AuditLogRecord.billing_cycle_id == None)  # noqa: E711
                .values(billing_cycle_id=billing_cycle_id)
            )

            for account in self.session.scalars(select(Account).options(joinedload(Accoun.owner))):
                if account.balance > 0:
                    payout_audit_log_record = AuditLogRecord(
                        account=account,
                        credit=account.balance,
                        info={"reason": "payout"},
                    )
                    self.session.add(payout_audit_log_record)
                    self.flush()

                    # TODO: replace with SMTP call to send email
                    print(f"to {account.user.email}: You got paid {account.balance}!")
