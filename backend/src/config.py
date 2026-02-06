import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv('.env.local')


class Settings(BaseSettings):
    database_url: str = os.getenv('DATABASE_URL', '') or 'sqlite:///./stock.db'
    cors_origins: str = os.getenv('CORS_ORIGINS', '') or 'http://localhost:3847'
    mock_mode: bool = os.getenv('MOCK_MODE', 'true').lower() == 'true'

    # シグナル判定デフォルト値
    rsi_buy_threshold: int = 30
    rsi_sell_threshold: int = 70
    sma_short_period: int = 5
    sma_mid_period: int = 25
    sma_long_period: int = 75

    class Config:
        env_file = '.env.local'


settings = Settings()
