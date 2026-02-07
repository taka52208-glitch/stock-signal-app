from .stocks import router as stocks_router
from .settings import router as settings_router
from .transactions import router as transactions_router
from .alerts import router as alerts_router
from .risk import router as risk_router
from .backtests import router as backtests_router
from .brokerage import router as brokerage_router

__all__ = [
    'stocks_router', 'settings_router', 'transactions_router',
    'alerts_router', 'risk_router', 'backtests_router', 'brokerage_router',
]
