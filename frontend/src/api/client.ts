import { config } from '../config';
import type {
  Stock, StockDetail, ChartData, Settings, AddStockRequest,
  Transaction, TransactionRequest, Portfolio, Recommendations,
  Alert, AlertCreateRequest, AlertHistory, RiskRules,
  TradeEvaluation, Checklist, PriceSuggestions,
  BacktestSummary, BacktestCreateRequest, BacktestDetail, BacktestTrade, BacktestSnapshot,
  BrokerageConfig, BrokerageBalance, BrokeragePosition, OrderCreateRequest, Order,
  AutoTradeConfig, AutoTradeStockSetting, AutoTradeLog,
} from '../types';

const BASE_URL = config.apiUrl;

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // おすすめ銘柄取得
  getRecommendations: () => fetchApi<Recommendations>('/api/recommendations'),

  // 銘柄一覧取得
  getStocks: () => fetchApi<Stock[]>('/api/stocks'),

  // 銘柄追加
  addStock: (data: AddStockRequest) =>
    fetchApi<Stock>('/api/stocks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 銘柄削除
  deleteStock: (code: string) =>
    fetchApi<void>(`/api/stocks/${code}`, {
      method: 'DELETE',
    }),

  // 銘柄詳細取得
  getStockDetail: (code: string) => fetchApi<StockDetail>(`/api/stocks/${code}`),

  // チャートデータ取得
  getChartData: (code: string, period: string = '3m') =>
    fetchApi<ChartData[]>(`/api/stocks/${code}/chart?period=${period}`),

  // 設定取得
  getSettings: () => fetchApi<Settings>('/api/settings'),

  // 設定更新
  updateSettings: (data: Settings) =>
    fetchApi<Settings>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 手動更新トリガー
  triggerUpdate: () =>
    fetchApi<{ message: string }>('/api/update', {
      method: 'POST',
    }),

  // 取引履歴取得
  getTransactions: () => fetchApi<Transaction[]>('/api/transactions'),

  // 取引記録
  addTransaction: (data: TransactionRequest) =>
    fetchApi<Transaction>('/api/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 取引削除
  deleteTransaction: (id: number) =>
    fetchApi<void>(`/api/transactions/${id}`, {
      method: 'DELETE',
    }),

  // ポートフォリオ取得
  getPortfolio: () => fetchApi<Portfolio>('/api/transactions/portfolio'),

  // アラート
  getAlerts: () => fetchApi<Alert[]>('/api/alerts'),
  createAlert: (data: AlertCreateRequest) =>
    fetchApi<Alert>('/api/alerts', { method: 'POST', body: JSON.stringify(data) }),
  deleteAlert: (id: number) =>
    fetchApi<void>(`/api/alerts/${id}`, { method: 'DELETE' }),
  getAlertHistory: () => fetchApi<AlertHistory[]>('/api/alerts/history'),
  markAlertsRead: (ids: number[]) =>
    fetchApi<void>('/api/alerts/mark-read', { method: 'POST', body: JSON.stringify({ ids }) }),
  getUnreadAlertCount: () => fetchApi<{ count: number }>('/api/alerts/unread-count'),

  // リスク管理
  getRiskRules: () => fetchApi<RiskRules>('/api/risk/rules'),
  updateRiskRules: (data: Partial<RiskRules>) =>
    fetchApi<RiskRules>('/api/risk/rules', { method: 'PUT', body: JSON.stringify(data) }),
  evaluateTrade: (data: { code: string; tradeType: string; quantity: number; price: number }) =>
    fetchApi<TradeEvaluation>('/api/risk/evaluate-trade', { method: 'POST', body: JSON.stringify(data) }),
  getChecklist: (code: string) => fetchApi<Checklist>(`/api/risk/checklist/${code}`),
  getSuggestedPrices: (code: string) => fetchApi<PriceSuggestions>(`/api/risk/suggest-prices/${code}`),

  // バックテスト
  getBacktests: () => fetchApi<BacktestSummary[]>('/api/backtests'),
  createBacktest: (data: BacktestCreateRequest) =>
    fetchApi<BacktestDetail>('/api/backtests', { method: 'POST', body: JSON.stringify(data) }),
  getBacktest: (id: number) => fetchApi<BacktestDetail>(`/api/backtests/${id}`),
  deleteBacktest: (id: number) =>
    fetchApi<void>(`/api/backtests/${id}`, { method: 'DELETE' }),
  getBacktestTrades: (id: number) => fetchApi<BacktestTrade[]>(`/api/backtests/${id}/trades`),
  getBacktestSnapshots: (id: number) => fetchApi<BacktestSnapshot[]>(`/api/backtests/${id}/snapshots`),
  compareBacktests: (ids: number[]) =>
    fetchApi<{ backtests: BacktestDetail[] }>('/api/backtests/compare', {
      method: 'POST', body: JSON.stringify({ ids }),
    }),

  // 証券API
  getBrokerageConfig: () => fetchApi<BrokerageConfig>('/api/brokerage/config'),
  updateBrokerageConfig: (data: Partial<BrokerageConfig>) =>
    fetchApi<BrokerageConfig>('/api/brokerage/config', { method: 'PUT', body: JSON.stringify(data) }),
  connectBrokerage: () =>
    fetchApi<{ connected: boolean; message: string }>('/api/brokerage/connect', { method: 'POST' }),
  getBrokerageBalance: () => fetchApi<BrokerageBalance>('/api/brokerage/balance'),
  getBrokeragePositions: () => fetchApi<BrokeragePosition[]>('/api/brokerage/positions'),
  getOrders: () => fetchApi<Order[]>('/api/brokerage/orders'),
  createOrder: (data: OrderCreateRequest) =>
    fetchApi<Order>('/api/brokerage/orders', { method: 'POST', body: JSON.stringify(data) }),
  cancelOrder: (id: number) =>
    fetchApi<void>(`/api/brokerage/orders/${id}`, { method: 'DELETE' }),
  syncBrokerage: () =>
    fetchApi<{ message: string }>('/api/brokerage/sync', { method: 'POST' }),

  // 自動売買
  getAutoTradeConfig: () => fetchApi<AutoTradeConfig>('/api/auto-trade/config'),
  updateAutoTradeConfig: (data: Partial<AutoTradeConfig>) =>
    fetchApi<AutoTradeConfig>('/api/auto-trade/config', { method: 'PUT', body: JSON.stringify(data) }),
  toggleAutoTrade: (enabled: boolean) =>
    fetchApi<AutoTradeConfig>('/api/auto-trade/toggle', { method: 'POST', body: JSON.stringify({ enabled }) }),
  getAutoTradeLog: (limit: number = 50) =>
    fetchApi<AutoTradeLog[]>(`/api/auto-trade/log?limit=${limit}`),
  getAutoTradeStocks: () => fetchApi<AutoTradeStockSetting[]>('/api/auto-trade/stocks'),
  updateAutoTradeStock: (code: string, enabled: boolean) =>
    fetchApi<AutoTradeStockSetting>(`/api/auto-trade/stocks/${code}`, {
      method: 'PUT', body: JSON.stringify({ enabled }),
    }),
};
