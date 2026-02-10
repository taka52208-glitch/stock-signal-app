import httpx
from sqlalchemy.orm import Session
from src.models.stock import BrokerageConfig, BrokerageOrder, Stock, Transaction

DEFAULT_CONFIG = {
    'host': 'localhost',
    'port': '18080',
    'apiPassword': '',
}


class KabuStationClient:
    """kabu STATION API クライアント"""

    def __init__(self, host: str, port: int, api_password: str):
        self.base_url = f'http://{host}:{port}/kabusapi'
        self.api_password = api_password
        self.token: str | None = None

    async def connect(self) -> str:
        """APIトークンを取得"""
        async with httpx.AsyncClient(headers={'Host': 'localhost'}) as client:
            resp = await client.post(
                f'{self.base_url}/token',
                json={'APIPassword': self.api_password},
            )
            resp.raise_for_status()
            data = resp.json()
            self.token = data.get('Token')
            return self.token

    def _headers(self) -> dict:
        return {'X-API-KEY': self.token or '', 'Host': 'localhost'}

    async def get_balance(self) -> dict:
        """残高照会"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'{self.base_url}/wallet/cash',
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def get_positions(self) -> list[dict]:
        """保有銘柄照会"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f'{self.base_url}/positions',
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def send_order(self, code: str, side: str, quantity: int,
                         order_type: str, price: float | None = None) -> dict:
        """注文送信"""
        # kabu STATION APIの注文パラメータ
        side_map = {'buy': '2', 'sell': '1'}
        front_order_type_map = {
            'market': '10',   # 成行
            'limit': '20',    # 指値
            'stop': '30',     # 逆指値
        }

        order_data = {
            'Password': self.api_password,
            'Symbol': f'{code}@1',  # 東証
            'Exchange': 1,  # 東証
            'SecurityType': 1,  # 株式
            'Side': side_map.get(side, '2'),
            'CashMargin': 1,  # 現物
            'DelivType': 2,  # お預り金
            'AccountType': 2,  # 特定
            'Qty': quantity,
            'FrontOrderType': front_order_type_map.get(order_type, '10'),
            'Price': price or 0,
            'ExpireDay': 0,  # 当日
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{self.base_url}/sendorder',
                headers=self._headers(),
                json=order_data,
            )
            resp.raise_for_status()
            return resp.json()

    async def cancel_order(self, order_id: str) -> dict:
        """注文取消"""
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f'{self.base_url}/cancelorder',
                headers=self._headers(),
                json={
                    'OrderId': order_id,
                    'Password': self.api_password,
                },
            )
            resp.raise_for_status()
            return resp.json()


class BrokerageService:
    def __init__(self, db: Session):
        self.db = db

    def get_config(self) -> dict:
        """接続設定を取得"""
        result = dict(DEFAULT_CONFIG)
        db_config = self.db.query(BrokerageConfig).all()
        for c in db_config:
            result[c.key] = c.value
        return {
            'host': result['host'],
            'port': int(result['port']),
            'apiPassword': result['apiPassword'],
        }

    def update_config(self, data: dict) -> dict:
        """接続設定を更新"""
        for key, value in data.items():
            if key not in DEFAULT_CONFIG:
                continue
            config = self.db.query(BrokerageConfig).filter(BrokerageConfig.key == key).first()
            if config:
                config.value = str(value)
            else:
                self.db.add(BrokerageConfig(key=key, value=str(value)))
        self.db.commit()
        return self.get_config()

    def _get_client(self) -> KabuStationClient:
        """クライアントを取得"""
        config = self.get_config()
        return KabuStationClient(config['host'], config['port'], config['apiPassword'])

    async def connect(self) -> dict:
        """接続テスト"""
        client = self._get_client()
        try:
            token = await client.connect()
            return {'connected': True, 'message': f'接続成功（トークン取得済み）'}
        except httpx.ConnectError:
            return {'connected': False, 'message': 'kabu STATIONに接続できません。アプリが起動しているか確認してください。'}
        except httpx.HTTPStatusError as e:
            return {'connected': False, 'message': f'認証エラー: {e.response.status_code}'}
        except Exception as e:
            return {'connected': False, 'message': f'接続エラー: {str(e)}'}

    async def get_balance(self) -> dict:
        """残高照会"""
        client = self._get_client()
        await client.connect()
        data = await client.get_balance()
        return {
            'cashBalance': data.get('StockAccountWallet', 0),
            'marginBalance': data.get('MarginAccountWallet', 0),
            'totalValue': data.get('StockAccountWallet', 0),
        }

    async def get_positions(self) -> list[dict]:
        """保有銘柄照会"""
        client = self._get_client()
        await client.connect()
        positions = await client.get_positions()
        result = []
        for pos in positions:
            code = pos.get('Symbol', '').split('@')[0] if '@' in pos.get('Symbol', '') else pos.get('Symbol', '')
            stock = self.db.query(Stock).filter(Stock.code == code).first()
            result.append({
                'code': code,
                'name': stock.name if stock else pos.get('SymbolName', f'銘柄{code}'),
                'quantity': pos.get('LeavesQty', 0),
                'averagePrice': pos.get('AveragePrice', 0),
                'currentPrice': pos.get('CurrentPrice', 0),
                'profitLoss': pos.get('ProfitLoss', 0),
            })
        return result

    def get_orders(self) -> list[dict]:
        """注文一覧を取得"""
        orders = self.db.query(BrokerageOrder).order_by(BrokerageOrder.created_at.desc()).all()
        return [{
            'id': o.id,
            'code': o.code,
            'orderType': o.order_type,
            'side': o.side,
            'quantity': o.quantity,
            'price': o.price,
            'status': o.status,
            'brokerageOrderId': o.brokerage_order_id,
            'createdAt': o.created_at.isoformat() if o.created_at else '',
            'updatedAt': o.updated_at.isoformat() if o.updated_at else '',
        } for o in orders]

    async def create_order(self, code: str, order_type: str, side: str,
                           quantity: int, price: float | None = None) -> dict:
        """注文を送信"""
        # DB記録を先に作成
        order = BrokerageOrder(
            code=code,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            status='pending',
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        try:
            client = self._get_client()
            await client.connect()
            result = await client.send_order(code, side, quantity, order_type, price)

            order.brokerage_order_id = result.get('OrderId')
            order.status = 'submitted'
            self.db.commit()
        except Exception as e:
            order.status = 'failed'
            self.db.commit()
            print(f"Order failed: {e}")

        return {
            'id': order.id,
            'code': order.code,
            'orderType': order.order_type,
            'side': order.side,
            'quantity': order.quantity,
            'price': order.price,
            'status': order.status,
            'brokerageOrderId': order.brokerage_order_id,
            'createdAt': order.created_at.isoformat() if order.created_at else '',
            'updatedAt': order.updated_at.isoformat() if order.updated_at else '',
        }

    async def cancel_order(self, order_id: int) -> bool:
        """注文をキャンセル"""
        order = self.db.query(BrokerageOrder).filter(BrokerageOrder.id == order_id).first()
        if not order:
            return False

        if order.brokerage_order_id:
            try:
                client = self._get_client()
                await client.connect()
                await client.cancel_order(order.brokerage_order_id)
            except Exception as e:
                print(f"Cancel failed: {e}")

        order.status = 'cancelled'
        self.db.commit()
        return True

    async def sync_positions(self) -> dict:
        """証券口座のポジションをポートフォリオと同期"""
        positions = await self.get_positions()
        synced = 0
        for pos in positions:
            if pos['quantity'] > 0:
                synced += 1
        return {'message': f'{synced}銘柄のポジション情報を取得しました'}
