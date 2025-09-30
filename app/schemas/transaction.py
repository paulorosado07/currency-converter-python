from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime


class ConvertRequest(BaseModel):
    fromCurrency: str = Field(..., examples=["USD"])
    toCurrency: str = Field(..., examples=["BRL"])
    amount: Decimal = Field(..., gt=0)


class TransactionDTO(BaseModel):
    transactionId: int
    userId: int
    fromCurrency: str
    toCurrency: str
    fromValue: Decimal
    toValue: Decimal
    rate: Decimal
    timestamp: datetime

    class Config:
        from_attributes = True
