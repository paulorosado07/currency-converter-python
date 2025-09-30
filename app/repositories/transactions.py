from sqlalchemy.orm import Session
from app.db.models import Transaction
from decimal import Decimal
from datetime import datetime


class TransactionRepository:
    @staticmethod
    def create(
        db: Session,
        *,
        user_id: int,
        from_currency: str,
        to_currency: str,
        from_value: Decimal,
        to_value: Decimal,
        rate: Decimal,
        timestamp: datetime,
    ) -> Transaction:
        tx = Transaction(
            user_id=user_id,
            from_currency=from_currency,
            to_currency=to_currency,
            from_value=from_value,
            to_value=to_value,
            rate=rate,
            timestamp=timestamp,
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx

    @staticmethod
    def list_by_user(db: Session, user_id: int) -> list[Transaction]:
        return (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.timestamp.desc())
            .all()
        )
