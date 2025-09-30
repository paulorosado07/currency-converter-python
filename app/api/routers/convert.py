from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.transaction import ConvertRequest, TransactionDTO
from app.services.transactions import transaction_service
from app.services.currency import CurrencyService

router = APIRouter(prefix="/convert", tags=["convert"])


@router.post("", response_model=TransactionDTO)
async def convert(
    payload: ConvertRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    tx = await transaction_service.convert_and_record(
        db,
        user_id=user.id,
        from_currency=payload.fromCurrency,
        to_currency=payload.toCurrency,
        amount=payload.amount,
    )
    # Map ORM → DTO with display quantization
    return TransactionDTO(
        transactionId=tx.transaction_id,
        userId=tx.user_id,
        fromCurrency=tx.from_currency,
        toCurrency=tx.to_currency,
        fromValue=CurrencyService.quantize_for_display(tx.from_value, tx.from_currency),
        toValue=CurrencyService.quantize_for_display(tx.to_value, tx.to_currency),
        rate=tx.rate,
        timestamp=tx.timestamp,
    )
