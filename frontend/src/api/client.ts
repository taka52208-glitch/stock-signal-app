import { config } from '../config';
import type { Stock, StockDetail, ChartData, Settings, AddStockRequest, Transaction, TransactionRequest, Portfolio } from '../types';

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
};
