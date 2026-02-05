import { create } from 'zustand';
import type { Stock, Settings } from '../types';

interface StockStore {
  stocks: Stock[];
  settings: Settings;
  isLoading: boolean;
  error: string | null;
  setStocks: (stocks: Stock[]) => void;
  setSettings: (settings: Settings) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  addStock: (stock: Stock) => void;
  removeStock: (code: string) => void;
}

const DEFAULT_SETTINGS: Settings = {
  rsiBuyThreshold: 30,
  rsiSellThreshold: 70,
  smaShortPeriod: 5,
  smaMidPeriod: 25,
  smaLongPeriod: 75,
};

export const useStockStore = create<StockStore>((set) => ({
  stocks: [],
  settings: DEFAULT_SETTINGS,
  isLoading: false,
  error: null,
  setStocks: (stocks) => set({ stocks }),
  setSettings: (settings) => set({ settings }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  addStock: (stock) => set((state) => ({ stocks: [...state.stocks, stock] })),
  removeStock: (code) => set((state) => ({ stocks: state.stocks.filter((s) => s.code !== code) })),
}));
