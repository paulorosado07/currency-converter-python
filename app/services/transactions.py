from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from sqlalchemy.orm import Session

from app.core.config import settings
from app.middlewares.error_handler import AppError
from app.repositories.transactions import TransactionRepository
from app.services.currency import currency_service
from app.core.logging import log


class TransactionService:
    @staticmethod
    async def convert_and_record(
        db: Session,
        *,
        user_id: int,
        from_currency: str,
        to_currency: str,
        amount: Decimal,
    ):
        log.info("transaction.validate.start", amount=str(amount))

        if amount <= 0:
            log.warning("transaction.invalid_amount", reason="<=0")
            raise AppError(
                "INVALID_AMOUNT", "Amount must be greater than 0", status_code=400
            )
        if amount > settings.MAX_AMOUNT:
            log.warning("transaction.amount_too_large", max=str(settings.MAX_AMOUNT))
            raise AppError(
                "AMOUNT_TOO_LARGE",
                f"Amount exceeds max {settings.MAX_AMOUNT}",
                status_code=400,
            )

        log.info("transaction.rate.fetch")

        rate = await currency_service.get_rate(from_currency, to_currency)
        to_value = (amount * rate).quantize(Decimal("1e-10"), rounding=ROUND_HALF_EVEN)

        log.info(
            "transaction.rate.ok",
            rate=str(rate),
            from_value=str(amount),
            to_value=str(to_value),
        )

        now = datetime.now(timezone.utc)
        tx = TransactionRepository.create(
            db,
            user_id=user_id,
            from_currency=from_currency.upper(),
            to_currency=to_currency.upper(),
            from_value=amount,
            to_value=to_value,
            rate=rate,
            timestamp=now,
        )

        log.info(
            "transaction.created",
            transactionId=getattr(tx, "transaction_id", None),
            timestamp=now.isoformat(),
        )

        return tx


transaction_service = TransactionService()
