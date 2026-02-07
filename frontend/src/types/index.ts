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
