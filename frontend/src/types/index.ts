// シグナルタイプ
export type SignalType = 'buy' | 'sell' | 'hold';

// 銘柄情報
export interface Stock {
  id: number;
  code: string;
  name: string;
  currentPrice: number;
  previousClose: number;
  changePercent: number;
  signal: SignalType;
  rsi: number;
  signalStrength: number;
  activeSignals: string[];
  updatedAt: string;
}

// 銘柄詳細
export interface StockDetail extends Stock {
  macd: number;
  macdSignal: number;
  macdHistogram: number;
  sma5: number;
  sma25: number;
  sma75: number;
  targetPrice: number | null;
  stopLossPrice: number | null;
  supportPrice: number | null;
  resistancePrice: number | null;
}

// チャートデータ
export interface ChartData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma5?: number;
  sma25?: number;
  sma75?: number;
}

// 設定
export interface Settings {
  rsiBuyThreshold: number;
  rsiSellThreshold: number;
  smaShortPeriod: number;
  smaMidPeriod: number;
  smaLongPeriod: number;
  investmentBudget: number;
}

// おすすめ銘柄
export interface Recommendation {
  code: string;
  name: string;
  currentPrice: number;
  signal: 'buy' | 'sell';
  signalStrength: number;
  activeSignals: string[];
  targetPrice: number | null;
  stopLossPrice: number | null;
  suggestedQuantity: number | null;
  suggestedAmount: number | null;
  expectedProfit: number | null;
  expectedProfitPercent: number | null;
  riskAmount: number | null;
  rsi: number;
}

// おすすめ一覧レスポンス
export interface Recommendations {
  buyRecommendations: Recommendation[];
  sellRecommendations: Recommendation[];
  investmentBudget: number;
}

// APIレスポンス
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// 銘柄追加リクエスト
export interface AddStockRequest {
  code: string;
}

// 取引タイプ
export type TransactionType = 'buy' | 'sell';

// 取引記録
export interface Transaction {
  id: number;
  code: string;
  name: string;
  transactionType: TransactionType;
  quantity: number;
  price: number;
  totalAmount: number;
  transactionDate: string;
  memo?: string;
}

// 取引リクエスト
export interface TransactionRequest {
  code: string;
  transactionType: TransactionType;
  quantity: number;
  price: number;
  memo?: string;
}

// 保有株
export interface Holding {
  code: string;
  name: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  totalCost: number;
  currentValue: number;
  profitLoss: number;
  profitLossPercent: number;
}

// ポートフォリオ
export interface Portfolio {
  holdings: Holding[];
  totalCost: number;
  totalValue: number;
  totalProfitLoss: number;
  totalProfitLossPercent: number;
}

// アラート
export type AlertType = 'price_above' | 'price_below' | 'signal_change';

export interface Alert {
  id: number;
  code: string;
  name: string;
  alertType: AlertType;
  conditionValue: number | null;
  isActive: boolean;
  createdAt: string;
}

export interface AlertCreateRequest {
  code: string;
  alertType: AlertType;
  conditionValue?: number;
}

export interface AlertHistory {
  id: number;
  alertId: number;
  code: string;
  name: string;
  message: string;
  alertType: string;
  signalBefore: string | null;
  signalAfter: string | null;
  priceAtTrigger: number | null;
  isRead: boolean;
  triggeredAt: string;
}

// リスク管理
export interface RiskRules {
  maxPositionPercent: number;
  maxLossPerTrade: number;
  maxPortfolioLoss: number;
  maxOpenPositions: number;
}

export interface RiskWarning {
  level: 'error' | 'warning' | 'info';
  message: string;
}

export interface TradeEvaluation {
  passed: boolean;
  warnings: RiskWarning[];
  tradeAmount: number;
  currentPortfolioValue: number;
  activePositions: number;
}

export interface ChecklistItem {
  label: string;
  status: 'ok' | 'warning' | 'neutral';
  detail: string;
}

export interface Checklist {
  code: string;
  name: string;
  items: ChecklistItem[];
}

export interface PriceSuggestion {
  type: string;
  label: string;
  price: number;
  reason: string;
}

export interface PriceSuggestions {
  code: string;
  name: string;
  currentPrice: number;
  suggestions: PriceSuggestion[];
}

// バックテスト
export interface BacktestSummary {
  id: number;
  name: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  status: string;
  totalReturn: number | null;
  totalReturnPercent: number | null;
  createdAt: string;
}

export interface BacktestCreateRequest {
  name: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  codes: string[];
  strategyParams?: Record<string, unknown>;
}

export interface BacktestDetail {
  id: number;
  name: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  status: string;
  strategyParams: Record<string, unknown> | null;
  resultSummary: Record<string, unknown> | null;
  createdAt: string;
}

export interface BacktestTrade {
  id: number;
  code: string;
  tradeType: string;
  quantity: number;
  price: number;
  tradeDate: string;
  pnl: number | null;
}

export interface BacktestSnapshot {
  date: string;
  portfolioValue: number;
  cash: number;
}

// 証券API
export interface BrokerageConfig {
  host: string;
  port: number;
  apiPassword: string;
}

export interface BrokerageBalance {
  cashBalance: number;
  marginBalance: number;
  totalValue: number;
}

export interface BrokeragePosition {
  code: string;
  name: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  profitLoss: number;
}

export interface OrderCreateRequest {
  code: string;
  orderType: 'market' | 'limit' | 'stop';
  side: 'buy' | 'sell';
  quantity: number;
  price?: number;
}

export interface Order {
  id: number;
  code: string;
  orderType: string;
  side: string;
  quantity: number;
  price: number | null;
  status: string;
  brokerageOrderId: string | null;
  createdAt: string;
  updatedAt: string;
}
