import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import BudgetSetting from '../BudgetSetting';

describe('BudgetSetting', () => {
  it('現在の予算を表示する', () => {
    render(<BudgetSetting budget={1000000} onBudgetChange={() => {}} />);
    expect(screen.getByText('¥1,000,000')).toBeInTheDocument();
    expect(screen.getByText('投資予算')).toBeInTheDocument();
  });

  it('変更ボタンでダイアログを開く', async () => {
    const user = userEvent.setup();
    render(<BudgetSetting budget={500000} onBudgetChange={() => {}} />);
    await user.click(screen.getByText('変更'));
    expect(screen.getByText('投資予算を設定')).toBeInTheDocument();
  });

  it('プリセット金額を表示する', async () => {
    const user = userEvent.setup();
    render(<BudgetSetting budget={100000} onBudgetChange={() => {}} />);
    await user.click(screen.getByText('変更'));
    expect(screen.getByText('¥50,000')).toBeInTheDocument();
    expect(screen.getByText('¥1,000,000')).toBeInTheDocument();
  });
});
