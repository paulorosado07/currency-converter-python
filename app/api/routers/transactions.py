from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.schemas.transaction import TransactionDTO
from app.db.models import Transaction, User
from app.core.logging import log

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionDTO])
async def list_transactions(
    userId: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    log.info(
        "transactions.list.start", path_params={"userId": userId}, auth_user_id=user.id
    )

    userFound = db.query(User).filter(User.id == userId).first()

    if not userFound:
        log.warning(
            "transactions.list.user_not_found",
            path_params={"userId": userId},
            auth_user_id=user.id,
        )
        raise HTTPException(
            status_code=404,
            detail="Impossible to show the user's transaction list because the user does not exist.",
        )
    """
    ⚠️ Commented out for testing, showing transactions of all users. To restrict, re-enable the restriction.

    if user.id != userId:
        log.warning(
            "transactions.list.forbidden",
            reason="mismatched_user",
            path_user_id=userId,
            auth_user_id=user.id,
        )
        raise HTTPException(status_code=403, detail="Forbidden: mismatched user")
    """

    txs: list[Transaction] = (
        db.query(Transaction)
        .filter(Transaction.user_id == userId)
        .order_by(Transaction.timestamp.desc())
        .all()
    )

    log.info("transactions.list.fetched", count=len(txs), user_id=userId)

    result = [
        TransactionDTO(
            transactionId=tx.transaction_id,
            userId=tx.user_id,
            fromCurrency=tx.from_currency,
            toCurrency=tx.to_currency,
            fromValue=tx.from_value,
            toValue=tx.to_value,
            rate=tx.rate,
            timestamp=tx.timestamp,
        )
        for tx in txs
    ]

    log.info("transactions.list.success", count=len(result), user_id=userId)
    return result
