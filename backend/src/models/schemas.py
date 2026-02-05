from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, datetime


class AddStockRequest(BaseModel):
    code: str = Field(..., pattern=r'^\d{4}$')


class StockResponse(BaseModel):
    id: int
    code: str
    name: str
    currentPrice: float
    previousClose: float
    changePercent: float
    signal: Literal['buy', 'sell', 'hold']
    rsi: float
    updatedAt: str

    class Config:
        from_attributes = True


class StockDetailResponse(StockResponse):
    macd: float
    macdSignal: float
    macdHistogram: float
    sma5: float
    sma25: float
    sma75: float


class ChartDataResponse(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    sma5: Optional[float] = None
    sma25: Optional[float] = None
    sma75: Optional[float] = None


class SettingsRequest(BaseModel):
    rsiBuyThreshold: int = Field(..., ge=10, le=50)
    rsiSellThreshold: int = Field(..., ge=50, le=90)
    smaShortPeriod: int = Field(..., ge=1, le=50)
    smaMidPeriod: int = Field(..., ge=10, le=100)
    smaLongPeriod: int = Field(..., ge=50, le=200)


class SettingsResponse(BaseModel):
    rsiBuyThreshold: int
    rsiSellThreshold: int
    smaShortPeriod: int
    smaMidPeriod: int
    smaLongPeriod: int


class MessageResponse(BaseModel):
    message: str


# 取引関連
class TransactionRequest(BaseModel):
    code: str = Field(..., pattern=r'^\d{4}$')
    transactionType: Literal['buy', 'sell']
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    memo: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    code: str
    name: str
    transactionType: Literal['buy', 'sell']
    quantity: int
    price: float
    totalAmount: float
    transactionDate: str
    memo: Optional[str] = None

    class Config:
        from_attributes = True


class HoldingResponse(BaseModel):
    code: str
    name: str
    quantity: int
    averagePrice: float
    currentPrice: float
    totalCost: float
    currentValue: float
    profitLoss: float
    profitLossPercent: float


class PortfolioResponse(BaseModel):
    holdings: list[HoldingResponse]
    totalCost: float
    totalValue: float
    totalProfitLoss: float
    totalProfitLossPercent: float
