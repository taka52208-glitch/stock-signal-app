import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SignalStrengthDisplay from '../SignalStrengthDisplay';

describe('SignalStrengthDisplay', () => {
  it('強度3で「強」ラベルを表示する', () => {
    render(<SignalStrengthDisplay strength={3} />);
    expect(screen.getByText('強')).toBeInTheDocument();
  });

  it('強度2で「中」ラベルを表示する', () => {
    render(<SignalStrengthDisplay strength={2} />);
    expect(screen.getByText('中')).toBeInTheDocument();
  });

  it('強度1で「弱」ラベルを表示する', () => {
    render(<SignalStrengthDisplay strength={1} />);
    expect(screen.getByText('弱')).toBeInTheDocument();
  });

  it('強度0でラベルを表示しない', () => {
    const { container } = render(<SignalStrengthDisplay strength={0} />);
    // 星アイコンは3つ（全て空）
    expect(container.querySelectorAll('svg')).toHaveLength(3);
  });

  it('showLabel=falseでラベルを非表示にする', () => {
    render(<SignalStrengthDisplay strength={3} showLabel={false} />);
    expect(screen.queryByText('強')).not.toBeInTheDocument();
  });
});
