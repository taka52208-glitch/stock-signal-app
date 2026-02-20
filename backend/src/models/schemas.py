from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
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
    signalStrength: int = 0
    activeSignals: list[str] = []
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
    targetPrice: Optional[float] = None
    stopLossPrice: Optional[float] = None
    supportPrice: Optional[float] = None
    resistancePrice: Optional[float] = None


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
    investmentBudget: Optional[int] = Field(None, ge=10000, le=100000000)


class SettingsResponse(BaseModel):
    rsiBuyThreshold: int
    rsiSellThreshold: int
    smaShortPeriod: int
    smaMidPeriod: int
    smaLongPeriod: int
    investmentBudget: int


class RecommendationResponse(BaseModel):
    code: str
    name: str
    currentPrice: float
    signal: Literal['buy', 'sell']
    signalStrength: int
    activeSignals: list[str]
    targetPrice: Optional[float] = None
    stopLossPrice: Optional[float] = None
    suggestedQuantity: Optional[int] = None
    suggestedAmount: Optional[int] = None
    expectedProfit: Optional[float] = None
    expectedProfitPercent: Optional[float] = None
    riskAmount: Optional[float] = None
    rsi: float


class RecommendationsResponse(BaseModel):
    buyRecommendations: list[RecommendationResponse]
    sellRecommendations: list[RecommendationResponse]
    investmentBudget: int


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


# アラート関連
class AlertCreateRequest(BaseModel):
    code: str = Field(..., pattern=r'^\d{4}$')
    alertType: Literal['price_above', 'price_below', 'signal_change']
    conditionValue: Optional[float] = None


class AlertResponse(BaseModel):
    id: int
    code: str
    name: str
    alertType: str
    conditionValue: Optional[float] = None
    isActive: bool
    createdAt: str


class AlertHistoryResponse(BaseModel):
    id: int
    alertId: int
    code: str
    name: str
    message: str
    alertType: str
    signalBefore: Optional[str] = None
    signalAfter: Optional[str] = None
    priceAtTrigger: Optional[float] = None
    isRead: bool
    triggeredAt: str


class MarkReadRequest(BaseModel):
    ids: list[int]


class UnreadCountResponse(BaseModel):
    count: int


# リスク管理関連
class RiskRulesResponse(BaseModel):
    maxPositionPercent: float
    maxLossPerTrade: float
    maxPortfolioLoss: float
    maxOpenPositions: int


class RiskRulesUpdateRequest(BaseModel):
    maxPositionPercent: Optional[float] = Field(None, ge=1, le=100)
    maxLossPerTrade: Optional[float] = Field(None, ge=1, le=50)
    maxPortfolioLoss: Optional[float] = Field(None, ge=1, le=100)
    maxOpenPositions: Optional[int] = Field(None, ge=1, le=50)


class RiskWarning(BaseModel):
    level: Literal['error', 'warning', 'info']
    message: str


class TradeEvaluationRequest(BaseModel):
    code: str = Field(..., pattern=r'^\d{4}$')
    tradeType: Literal['buy', 'sell']
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class TradeEvaluationResponse(BaseModel):
    passed: bool
    warnings: list[RiskWarning]
    tradeAmount: float
    currentPortfolioValue: float
    activePositions: int


class ChecklistItem(BaseModel):
    label: str
    status: Literal['ok', 'warning', 'neutral']
    detail: str


class ChecklistResponse(BaseModel):
    code: str
    name: str
    items: list[ChecklistItem]


class PriceSuggestion(BaseModel):
    type: str
    label: str
    price: float
    reason: str


class PriceSuggestionsResponse(BaseModel):
    code: str
    name: str
    currentPrice: float
    suggestions: list[PriceSuggestion]


# バックテスト関連
class BacktestCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    startDate: str  # YYYY-MM-DD
    endDate: str
    initialCapital: float = Field(..., gt=0)
    codes: list[str]
    strategyParams: Optional[dict] = None


class BacktestSummary(BaseModel):
    id: int
    name: str
    startDate: str
    endDate: str
    initialCapital: float
    status: str
    totalReturn: Optional[float] = None
    totalReturnPercent: Optional[float] = None
    createdAt: str


class BacktestTradeResponse(BaseModel):
    id: int
    code: str
    tradeType: str
    quantity: int
    price: float
    tradeDate: str
    pnl: Optional[float] = None


class BacktestSnapshotResponse(BaseModel):
    date: str
    portfolioValue: float
    cash: float


class BacktestDetailResponse(BaseModel):
    id: int
    name: str
    startDate: str
    endDate: str
    initialCapital: float
    status: str
    strategyParams: Optional[dict] = None
    resultSummary: Optional[dict] = None
    createdAt: str


class BacktestCompareRequest(BaseModel):
    ids: list[int] = Field(..., min_length=2, max_length=5)


class BacktestCompareResponse(BaseModel):
    backtests: list[BacktestDetailResponse]


# 証券API関連
class BrokerageConfigResponse(BaseModel):
    host: str
    port: int
    apiPassword: str


class BrokerageConfigUpdateRequest(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    apiPassword: Optional[str] = None


class BrokerageConnectResponse(BaseModel):
    connected: bool
    message: str


class BrokerageBalanceResponse(BaseModel):
    cashBalance: float
    marginBalance: float
    totalValue: float


class BrokeragePositionResponse(BaseModel):
    code: str
    name: str
    quantity: int
    averagePrice: float
    currentPrice: float
    profitLoss: float


class OrderCreateRequest(BaseModel):
    code: str = Field(..., pattern=r'^\d{4}$')
    orderType: Literal['market', 'limit', 'stop']
    side: Literal['buy', 'sell']
    quantity: int = Field(..., gt=0)
    price: Optional[float] = None


class OrderResponse(BaseModel):
    id: int
    code: str
    orderType: str
    side: str
    quantity: int
    price: Optional[float] = None
    status: str
    brokerageOrderId: Optional[str] = None
    createdAt: str
    updatedAt: str


# 自動売買関連
class AutoTradeConfigResponse(BaseModel):
    enabled: bool
    minSignalStrength: int
    maxTradesPerDay: int
    orderType: str
    dryRun: bool


class AutoTradeConfigUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    minSignalStrength: Optional[int] = Field(None, ge=1, le=3)
    maxTradesPerDay: Optional[int] = Field(None, ge=1, le=20)
    orderType: Optional[Literal['market', 'limit']] = None
    dryRun: Optional[bool] = None


class AutoTradeToggleRequest(BaseModel):
    enabled: bool


class AutoTradeStockSettingResponse(BaseModel):
    code: str
    name: str
    enabled: bool


class AutoTradeStockUpdateRequest(BaseModel):
    enabled: bool


class VirtualHoldingResponse(BaseModel):
    code: str
    name: str
    quantity: int
    averagePrice: float
    currentPrice: float
    totalCost: float
    currentValue: float
    profitLoss: float
    profitLossPercent: float


class VirtualPortfolioResponse(BaseModel):
    holdings: list[VirtualHoldingResponse]
    totalCost: float
    totalValue: float
    totalProfitLoss: float
    totalProfitLossPercent: float
    realizedProfitLoss: float
    unrealizedProfitLoss: float
    tradeCount: int


class AutoTradeLogResponse(BaseModel):
    id: int
    code: str
    signalType: str
    signalStrength: Optional[int] = None
    activeSignals: list[str]
    orderType: Optional[str] = None
    orderPrice: Optional[float] = None
    quantity: Optional[int] = None
    riskPassed: Optional[bool] = None
    riskWarnings: Optional[list] = None
    executed: bool
    dryRun: bool
    resultStatus: str
    resultMessage: Optional[str] = None
    transactionId: Optional[int] = None
    brokerageOrderId: Optional[str] = None
    createdAt: str
