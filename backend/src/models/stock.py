from sqlalchemy import Column, Integer, String, Float, Date, DateTime, BigInteger, Boolean, Text
from sqlalchemy.sql import func
from .database import Base


class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class StockPrice(Base):
    __tablename__ = 'stock_prices'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), index=True, nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)


class Signal(Base):
    __tablename__ = 'signals'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), index=True, nullable=False)
    date = Column(Date, nullable=False)
    signal_type = Column(String(10), nullable=False)  # buy, sell, hold
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    sma5 = Column(Float)
    sma25 = Column(Float)
    sma75 = Column(Float)
    signal_strength = Column(Integer, nullable=True)  # 1〜3
    active_signals = Column(String(100), nullable=True)  # カンマ区切り: "RSI,MACD,GoldenCross"
    target_price = Column(Float, nullable=True)
    stop_loss_price = Column(Float, nullable=True)
    support_price = Column(Float, nullable=True)
    resistance_price = Column(Float, nullable=True)


class Setting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(100), nullable=False)


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), index=True, nullable=False)
    transaction_type = Column(String(4), nullable=False)  # buy, sell
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    transaction_date = Column(DateTime, server_default=func.now())
    memo = Column(String(200), nullable=True)


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), index=True, nullable=False)
    alert_type = Column(String(20), nullable=False)  # price_above, price_below, signal_change
    condition_value = Column(Float, nullable=True)  # 価格条件（signal_changeの場合はNULL）
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class AlertHistory(Base):
    __tablename__ = 'alert_history'

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, index=True, nullable=False)
    code = Column(String(10), index=True, nullable=False)
    message = Column(String(500), nullable=False)
    alert_type = Column(String(20), nullable=False)
    signal_before = Column(String(10), nullable=True)
    signal_after = Column(String(10), nullable=True)
    price_at_trigger = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    triggered_at = Column(DateTime, server_default=func.now())


class RiskRule(Base):
    __tablename__ = 'risk_rules'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(100), nullable=False)


class Backtest(Base):
    __tablename__ = 'backtests'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Float, nullable=False)
    strategy_params = Column(Text, nullable=True)  # JSON
    result_summary = Column(Text, nullable=True)  # JSON
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    created_at = Column(DateTime, server_default=func.now())


class BacktestTrade(Base):
    __tablename__ = 'backtest_trades'

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, index=True, nullable=False)
    code = Column(String(10), nullable=False)
    trade_type = Column(String(4), nullable=False)  # buy, sell
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    trade_date = Column(Date, nullable=False)
    pnl = Column(Float, nullable=True)


class BacktestSnapshot(Base):
    __tablename__ = 'backtest_snapshots'

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, index=True, nullable=False)
    date = Column(Date, nullable=False)
    portfolio_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)


class BrokerageConfig(Base):
    __tablename__ = 'brokerage_config'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(200), nullable=False)


class BrokerageOrder(Base):
    __tablename__ = 'brokerage_orders'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), index=True, nullable=False)
    order_type = Column(String(20), nullable=False)  # market, limit, stop
    side = Column(String(4), nullable=False)  # buy, sell
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=True)
    status = Column(String(20), default='pending')  # pending, submitted, filled, cancelled, failed
    brokerage_order_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
