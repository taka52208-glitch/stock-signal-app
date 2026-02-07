from sqlalchemy import Column, Integer, String, Float, Date, DateTime, BigInteger
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
