from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, cast, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload, selectinload

from .event_producer import AccountCreatedV1, AccountUpdatedV1, send_events
from .db import Session
from .models import Account, AuditLogRecord, AuditLogRecordReason


class AccountingService:
    def __init__(self, session: Session):
        self.session = session

    def get_stats(self, stats_date: date):
        query = select(
            # management earnings = total credit - total debit
            (
                func.coalesce(func.sum(AuditLogRecord.credit), 0)
                - func.coalesce(func.sum(AuditLogRecord.debit), 0)
            ).label("earnings"),
        ).filter(
            AuditLogRecord.reason != AuditLogRecordReason.payout,
            cast(AuditLogRecord.created_at, Date) == stats_date,
        )
        return self.session.execute(query).one()

    def get_account(self, user_public_id: str):
        query = (
            select(Account)
            .filter_by(owner_public_id=user_public_id)
            .options(selectinload(Account.audit_log_records))
        )
        return self.session.scalars(query).one_or_none()

    # TODO: rework event consumer logic to guarantee that Account is created
    # before balance changes are applied to it
    def _upsert_account(self, owner_public_id: str, balance_diff: Decimal) -> Account:
        return self.session.scalars(
            insert(Account)
            .values(
                owner_public_id=owner_public_id,
                balance=balance_diff,
            )
            .on_conflict_do_update(
                index_elements=[Account.owner_public_id],
                set_={Account.balance: Account.balance + balance_diff},
            )
            .returning(Account)
        ).one()

    def create_account(self, owner_public_id: str):
        with self.session.begin():
            account = self._upsert_account(owner_public_id, 0)
            send_events([AccountCreatedV1.from_account(account)])
        return account

    def debit_account(
        self,
        owner_public_id: str,
        amount: Decimal,
        reason: AuditLogRecordReason,
        info: Optional[dict] = None,
    ):
        with self.session.begin():
            account = self._upsert_account(
                owner_public_id=owner_public_id,
                balance_diff=amount,
            )

            self.session.add(
                AuditLogRecord(
                    account_id=account.id,
                    debit=amount,
                    reason=reason,
                    info=info,
                )
            )
            self.session.flush()

            send_events([AccountUpdatedV1.from_account(account)])

    def credit_account(
        self,
        owner_public_id: str,
        amount: Decimal,
        reason: AuditLogRecordReason,
        info: Optional[dict] = None,
    ):
        with self.session.begin():
            account = self._upsert_account(
                owner_public_id=owner_public_id,
                balance_diff=-amount,
            )

            self.session.add(
                AuditLogRecord(
                    account_id=account.id,
                    credit=amount,
                    reason=reason,
                    info=info,
                )
            )
            self.session.flush()

            send_events([AccountUpdatedV1.from_account(account)])

    def payout(self):
        # TODO: process accounts iteratively to avoid OOMs and long DB table locks
        payout_accounts_query = (
            select(Account)
            .where(Account.balance > 0)
            .with_for_update()
            .options(joinedload(Account.owner))
        )
        with self.session.begin():
            unpaid_accounts = self.session.scalars(payout_accounts_query).all()
            for account in unpaid_accounts:
                old_balance = account.balance
                account.balance = 0
                self.session.add(
                    AuditLogRecord(
                        account=account,
                        credit=old_balance,
                        reason=AuditLogRecordReason.payout,
                    )
                )
                # TODO: send account balance changed event
                # TODO: replace with SMTP call to send email
                print(f"{account.user.email} got paid {old_balance}.")

            send_events(
                [AccountUpdatedV1.from_account(account) for account in unpaid_accounts]
            )
