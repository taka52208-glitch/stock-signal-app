import json
import numpy as np
import pandas as pd
from datetime import datetime, date
from sqlalchemy.orm import Session
from src.models.stock import Backtest, BacktestTrade, BacktestSnapshot, Stock, StockPrice
from src.services.stock_service import StockService


class BacktestService:
    def __init__(self, db: Session):
        self.db = db

    def get_backtests(self) -> list[dict]:
        """バックテスト一覧を取得"""
        tests = self.db.query(Backtest).order_by(Backtest.created_at.desc()).all()
        result = []
        for t in tests:
            summary = json.loads(t.result_summary) if t.result_summary else None
            result.append({
                'id': t.id,
                'name': t.name,
                'startDate': t.start_date.isoformat(),
                'endDate': t.end_date.isoformat(),
                'initialCapital': t.initial_capital,
                'status': t.status,
                'totalReturn': summary.get('totalReturn') if summary else None,
                'totalReturnPercent': summary.get('totalReturnPercent') if summary else None,
                'createdAt': t.created_at.isoformat() if t.created_at else '',
            })
        return result

    def create_backtest(self, name: str, start_date: str, end_date: str,
                        initial_capital: float, codes: list[str],
                        strategy_params: dict | None = None) -> dict:
        """バックテストを作成し実行"""
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        params = strategy_params or {}
        params['codes'] = codes

        backtest = Backtest(
            name=name,
            start_date=start,
            end_date=end,
            initial_capital=initial_capital,
            strategy_params=json.dumps(params),
            status='running',
        )
        self.db.add(backtest)
        self.db.commit()
        self.db.refresh(backtest)

        try:
            self._run_backtest(backtest, codes)
            backtest.status = 'completed'
        except Exception as e:
            backtest.status = 'failed'
            backtest.result_summary = json.dumps({'error': str(e)})
            print(f"Backtest failed: {e}")
        self.db.commit()

        return self._format_detail(backtest)

    def _run_backtest(self, backtest: Backtest, codes: list[str]):
        """バックテストを実行"""
        stock_service = StockService(self.db)
        settings = stock_service.get_settings()

        cash = backtest.initial_capital
        positions: dict[str, dict] = {}  # code -> {quantity, avg_price}
        all_trades: list[dict] = []

        # 各銘柄の株価データを取得（DB内のデータを使用）
        stock_data: dict[str, pd.DataFrame] = {}
        for code in codes:
            prices = self.db.query(StockPrice).filter(
                StockPrice.code == code,
                StockPrice.date >= backtest.start_date,
                StockPrice.date <= backtest.end_date,
            ).order_by(StockPrice.date.asc()).all()

            if not prices:
                continue

            df = pd.DataFrame([{
                'date': p.date, 'open': p.open, 'high': p.high,
                'low': p.low, 'close': p.close, 'volume': p.volume,
            } for p in prices])

            if len(df) >= 26:
                df = stock_service.calculate_indicators(df, settings)
            stock_data[code] = df

        if not stock_data:
            raise ValueError('指定期間のデータがありません')

        # 全日付を収集
        all_dates = set()
        for df in stock_data.values():
            for d in df['date']:
                if isinstance(d, datetime):
                    d = d.date()
                all_dates.add(d)
        sorted_dates = sorted(all_dates)

        # 日次シミュレーション
        for current_date in sorted_dates:
            for code, df in stock_data.items():
                date_rows = df[df['date'].apply(
                    lambda x: x.date() if isinstance(x, datetime) else x
                ) == current_date]
                if date_rows.empty:
                    continue

                idx = df.index.get_loc(date_rows.index[0])
                if idx < 1:
                    continue

                # シグナル計算（直近2日分のデータで判定）
                sub_df = df.iloc[:idx + 1]
                if len(sub_df) < 26:
                    continue

                details = stock_service.calculate_signal_details(sub_df, settings)
                current_price = float(df.iloc[idx]['close'])

                if details['signal_type'] == 'buy' and code not in positions:
                    # 買い: 資金の1/銘柄数で配分
                    budget_per_stock = cash / max(len(codes) - len(positions), 1)
                    quantity = int(budget_per_stock / current_price) if current_price > 0 else 0
                    if quantity > 0:
                        cost = quantity * current_price
                        cash -= cost
                        positions[code] = {'quantity': quantity, 'avg_price': current_price}
                        all_trades.append({
                            'code': code, 'trade_type': 'buy', 'quantity': quantity,
                            'price': current_price, 'trade_date': current_date, 'pnl': None,
                        })

                elif details['signal_type'] == 'sell' and code in positions:
                    # 売り
                    pos = positions[code]
                    proceeds = pos['quantity'] * current_price
                    pnl = proceeds - (pos['quantity'] * pos['avg_price'])
                    cash += proceeds
                    all_trades.append({
                        'code': code, 'trade_type': 'sell', 'quantity': pos['quantity'],
                        'price': current_price, 'trade_date': current_date, 'pnl': round(pnl, 2),
                    })
                    del positions[code]

            # 日次スナップショット
            portfolio_value = cash
            for code, pos in positions.items():
                df = stock_data.get(code)
                if df is not None:
                    date_rows = df[df['date'].apply(
                        lambda x: x.date() if isinstance(x, datetime) else x
                    ) == current_date]
                    if not date_rows.empty:
                        portfolio_value += pos['quantity'] * float(date_rows.iloc[0]['close'])
                    else:
                        portfolio_value += pos['quantity'] * pos['avg_price']

            snapshot = BacktestSnapshot(
                backtest_id=backtest.id,
                date=current_date,
                portfolio_value=round(portfolio_value, 2),
                cash=round(cash, 2),
            )
            self.db.add(snapshot)

        # 取引記録を保存
        for t in all_trades:
            trade = BacktestTrade(
                backtest_id=backtest.id,
                code=t['code'],
                trade_type=t['trade_type'],
                quantity=t['quantity'],
                price=t['price'],
                trade_date=t['trade_date'],
                pnl=t.get('pnl'),
            )
            self.db.add(trade)

        # パフォーマンス計算
        snapshots = self.db.query(BacktestSnapshot).filter(
            BacktestSnapshot.backtest_id == backtest.id
        ).order_by(BacktestSnapshot.date.asc()).all()

        final_value = snapshots[-1].portfolio_value if snapshots else backtest.initial_capital
        total_return = final_value - backtest.initial_capital
        total_return_pct = (total_return / backtest.initial_capital) * 100

        # 最大ドローダウン
        peak = backtest.initial_capital
        max_dd = 0
        for s in snapshots:
            if s.portfolio_value > peak:
                peak = s.portfolio_value
            dd = (peak - s.portfolio_value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        # 勝率
        sell_trades = [t for t in all_trades if t['trade_type'] == 'sell' and t.get('pnl') is not None]
        wins = len([t for t in sell_trades if t['pnl'] > 0])
        win_rate = (wins / len(sell_trades) * 100) if sell_trades else 0

        # プロフィットファクター
        gross_profit = sum(t['pnl'] for t in sell_trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in sell_trades if t['pnl'] < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0

        # シャープレシオ（日次リターン）
        if len(snapshots) >= 2:
            daily_returns = []
            for i in range(1, len(snapshots)):
                r = (snapshots[i].portfolio_value - snapshots[i - 1].portfolio_value) / snapshots[i - 1].portfolio_value
                daily_returns.append(r)
            if daily_returns:
                mean_r = np.mean(daily_returns)
                std_r = np.std(daily_returns)
                risk_free_daily = 0.001 / 252  # 年率0.1%
                sharpe = ((mean_r - risk_free_daily) / std_r * np.sqrt(252)) if std_r > 0 else 0
            else:
                sharpe = 0
        else:
            sharpe = 0

        summary = {
            'totalReturn': round(total_return, 2),
            'totalReturnPercent': round(total_return_pct, 2),
            'finalValue': round(final_value, 2),
            'maxDrawdown': round(max_dd, 2),
            'winRate': round(win_rate, 1),
            'totalTrades': len(all_trades),
            'profitFactor': round(profit_factor, 2) if profit_factor != float('inf') else 999.99,
            'sharpeRatio': round(sharpe, 2),
        }
        backtest.result_summary = json.dumps(summary)

    def get_backtest(self, backtest_id: int) -> dict | None:
        """バックテスト詳細を取得"""
        bt = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not bt:
            return None
        return self._format_detail(bt)

    def delete_backtest(self, backtest_id: int) -> bool:
        """バックテストを削除"""
        bt = self.db.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not bt:
            return False
        self.db.query(BacktestTrade).filter(BacktestTrade.backtest_id == backtest_id).delete()
        self.db.query(BacktestSnapshot).filter(BacktestSnapshot.backtest_id == backtest_id).delete()
        self.db.delete(bt)
        self.db.commit()
        return True

    def get_trades(self, backtest_id: int) -> list[dict]:
        """バックテストの取引一覧"""
        trades = self.db.query(BacktestTrade).filter(
            BacktestTrade.backtest_id == backtest_id
        ).order_by(BacktestTrade.trade_date.asc()).all()
        return [{
            'id': t.id,
            'code': t.code,
            'tradeType': t.trade_type,
            'quantity': t.quantity,
            'price': t.price,
            'tradeDate': t.trade_date.isoformat(),
            'pnl': t.pnl,
        } for t in trades]

    def get_snapshots(self, backtest_id: int) -> list[dict]:
        """バックテストの資産推移"""
        snapshots = self.db.query(BacktestSnapshot).filter(
            BacktestSnapshot.backtest_id == backtest_id
        ).order_by(BacktestSnapshot.date.asc()).all()
        return [{
            'date': s.date.isoformat(),
            'portfolioValue': s.portfolio_value,
            'cash': s.cash,
        } for s in snapshots]

    def compare_backtests(self, ids: list[int]) -> list[dict]:
        """複数バックテストの比較"""
        backtests = self.db.query(Backtest).filter(Backtest.id.in_(ids)).all()
        return [self._format_detail(bt) for bt in backtests]

    def _format_detail(self, bt: Backtest) -> dict:
        """バックテスト詳細のフォーマット"""
        return {
            'id': bt.id,
            'name': bt.name,
            'startDate': bt.start_date.isoformat(),
            'endDate': bt.end_date.isoformat(),
            'initialCapital': bt.initial_capital,
            'status': bt.status,
            'strategyParams': json.loads(bt.strategy_params) if bt.strategy_params else None,
            'resultSummary': json.loads(bt.result_summary) if bt.result_summary else None,
            'createdAt': bt.created_at.isoformat() if bt.created_at else '',
        }
