import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import BuyRecommendationCard from '../BuyRecommendationCard';
import type { Recommendation } from '../../types';

const mockRec: Recommendation = {
  code: '7203',
  name: 'トヨタ自動車',
  currentPrice: 3000,
  signal: 'buy',
  signalStrength: 2,
  activeSignals: ['RSI', 'MACD'],
  targetPrice: 3200,
  stopLossPrice: 2800,
  suggestedQuantity: 10,
  suggestedAmount: 30000,
  expectedProfit: 2000,
  expectedProfitPercent: 6.7,
  riskAmount: 2000,
  rsi: 28,
};

function renderCard(rec: Recommendation = mockRec) {
  return render(
    <MemoryRouter>
      <BuyRecommendationCard recommendation={rec} />
    </MemoryRouter>
  );
}

describe('BuyRecommendationCard', () => {
  it('銘柄コードと名前を表示する', () => {
    renderCard();
    expect(screen.getByText('7203')).toBeInTheDocument();
    expect(screen.getByText('トヨタ自動車')).toBeInTheDocument();
  });

  it('現在価格を表示する', () => {
    renderCard();
    expect(screen.getByText('¥3,000')).toBeInTheDocument();
  });

  it('シグナルラベルを表示する', () => {
    renderCard();
    expect(screen.getByText('RSI売られすぎ')).toBeInTheDocument();
    expect(screen.getByText('MACDクロス')).toBeInTheDocument();
  });

  it('購入提案を表示する', () => {
    renderCard();
    expect(screen.getByText('購入提案')).toBeInTheDocument();
  });

  it('suggestedQuantityが0なら購入提案を非表示', () => {
    renderCard({ ...mockRec, suggestedQuantity: 0 });
    expect(screen.queryByText('購入提案')).not.toBeInTheDocument();
  });
});
