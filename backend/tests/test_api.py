"""API エンドポイント統合テスト"""
from src.models.stock import Stock, StockPrice, Signal, Transaction, RiskRule
from datetime import datetime


class TestHealthAPI:

    def test_health(self, client):
        res = client.get('/api/health')
        assert res.status_code == 200
        assert res.json()['status'] == 'healthy'


class TestStocksAPI:

    def test_get_stocks_empty(self, client):
        res = client.get('/api/stocks')
        assert res.status_code == 200
        assert res.json() == []

    def test_add_stock(self, client, db):
        res = client.post('/api/stocks', json={'code': '7203'})
        assert res.status_code == 200
        data = res.json()
        assert data['code'] == '7203'
        assert data['name'] == 'トヨタ自動車'

    def test_add_stock_invalid_code(self, client):
        res = client.post('/api/stocks', json={'code': 'ABCD'})
        assert res.status_code == 422

    def test_delete_stock(self, client, db):
        client.post('/api/stocks', json={'code': '7203'})
        res = client.delete('/api/stocks/7203')
        assert res.status_code == 200

    def test_delete_nonexistent_stock(self, client):
        res = client.delete('/api/stocks/9999')
        assert res.status_code == 404

    def test_get_stock_detail(self, client, db):
        client.post('/api/stocks', json={'code': '7203'})
        res = client.get('/api/stocks/7203')
        assert res.status_code == 200
        data = res.json()
        assert data['code'] == '7203'

    def test_get_stock_detail_not_found(self, client):
        res = client.get('/api/stocks/9999')
        assert res.status_code == 404

    def test_get_recommendations(self, client):
        res = client.get('/api/recommendations')
        assert res.status_code == 200


class TestSettingsAPI:

    def test_get_settings(self, client):
        res = client.get('/api/settings')
        assert res.status_code == 200
        data = res.json()
        assert 'rsiBuyThreshold' in data

    def test_update_settings(self, client):
        res = client.put('/api/settings', json={
            'rsiBuyThreshold': 35,
            'rsiSellThreshold': 65,
            'smaShortPeriod': 5,
            'smaMidPeriod': 25,
            'smaLongPeriod': 75,
        })
        assert res.status_code == 200
        assert res.json()['rsiBuyThreshold'] == 35


class TestTransactionsAPI:

    def test_get_transactions_empty(self, client):
        res = client.get('/api/transactions')
        assert res.status_code == 200
        assert res.json() == []

    def test_add_transaction(self, client, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.commit()
        res = client.post('/api/transactions', json={
            'code': '7203',
            'transactionType': 'buy',
            'quantity': 100,
            'price': 3000.0,
        })
        assert res.status_code == 200

    def test_get_portfolio(self, client, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.add(StockPrice(code='7203', date=datetime.now().date(),
                          open=3000, high=3030, low=2970, close=3000, volume=500000))
        db.commit()
        res = client.get('/api/transactions/portfolio')
        assert res.status_code == 200


class TestRiskAPI:

    def test_get_risk_rules(self, client):
        res = client.get('/api/risk/rules')
        assert res.status_code == 200
        data = res.json()
        assert 'maxOpenPositions' in data

    def test_update_risk_rules(self, client):
        res = client.put('/api/risk/rules', json={'maxOpenPositions': 5})
        assert res.status_code == 200
        assert res.json()['maxOpenPositions'] == 5

    def test_evaluate_trade(self, client, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.add(StockPrice(code='7203', date=datetime.now().date(),
                          open=3000, high=3030, low=2970, close=3000, volume=500000))
        db.commit()
        res = client.post('/api/risk/evaluate-trade', json={
            'code': '7203',
            'tradeType': 'buy',
            'quantity': 10,
            'price': 3000.0,
        })
        assert res.status_code == 200
        data = res.json()
        assert 'passed' in data

    def test_checklist(self, client, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.commit()
        res = client.get('/api/risk/checklist/7203')
        assert res.status_code == 200

    def test_suggest_prices(self, client, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.add(StockPrice(code='7203', date=datetime.now().date(),
                          open=3000, high=3030, low=2970, close=3000, volume=500000))
        db.commit()
        res = client.get('/api/risk/suggest-prices/7203')
        assert res.status_code == 200


class TestAutoTradeAPI:

    def test_get_config(self, client):
        res = client.get('/api/auto-trade/config')
        assert res.status_code == 200
        data = res.json()
        assert 'enabled' in data
        assert 'dryRun' in data

    def test_update_config(self, client):
        res = client.put('/api/auto-trade/config', json={'minSignalStrength': 2})
        assert res.status_code == 200
        assert res.json()['minSignalStrength'] == 2

    def test_toggle(self, client):
        res = client.post('/api/auto-trade/toggle', json={'enabled': False})
        assert res.status_code == 200
        assert res.json()['enabled'] is False

    def test_get_logs(self, client):
        res = client.get('/api/auto-trade/log')
        assert res.status_code == 200

    def test_get_stocks(self, client):
        res = client.get('/api/auto-trade/stocks')
        assert res.status_code == 200


class TestAlertsAPI:

    def test_get_alerts(self, client):
        res = client.get('/api/alerts')
        assert res.status_code == 200

    def test_create_alert(self, client, db):
        db.add(Stock(code='7203', name='トヨタ'))
        db.commit()
        res = client.post('/api/alerts', json={
            'code': '7203',
            'alertType': 'price_above',
            'conditionValue': 3500.0,
        })
        assert res.status_code == 200

    def test_unread_count(self, client):
        res = client.get('/api/alerts/unread-count')
        assert res.status_code == 200
