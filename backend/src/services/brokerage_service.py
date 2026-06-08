import asyncio
import logging
import subprocess
import time
from datetime import datetime

import httpx
from sqlalchemy.orm import Session
from src.models.stock import BrokerageConfig, BrokerageHealth, BrokerageOrder, Stock, Transaction

logger = logging.getLogger(__name__)

KABU_STATION_EXE = r'C:\Users\taka5\AppData\Local\kabuStation\KabuS.exe'
AUTO_LOGIN_SCRIPT = r'C:\Users\taka5\kabu_scripts\kabu_auto_login.ps1'
POWERSHELL_EXE = '/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'

# 最良執行方針対応（2026-03-02〜）で、現物・信用「新規」発注の市場コード 1(東証) は廃止された。
# 9(SOR) または 27(東証＋) を指定しないと kabu が Code=100378「現物買・売注文抑止エラー」で拒否する。
# 9(SOR)=複数市場で最良執行・手数料無料（推奨）。27(東証＋)=東証優先の特殊用途。
# 注意: 信用建玉の「返済」は従来どおり 1(東証) 必須だが、本コードは返済(CashMargin=3)未対応。
NEW_ORDER_EXCHANGE = 9  # SOR

DEFAULT_CONFIG = {
    'host': 'localhost',
    'port': '18080',
    'apiPassword': '',
    'loginId': '',
    'loginPassword': '',
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
            if resp.status_code == 401:
                body = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
                logger.error(
                    f"[kabu-api] 初回認証失敗(401): {body.get('Message', 'unknown')} "
                    f"(Code={body.get('Code', 'N/A')}). "
                    f"kabu STATIONの再起動が必要な可能性があります"
                )
            resp.raise_for_status()
            data = resp.json()
            self.token = data.get('Token')
            logger.info(f"[kabu-api] トークン取得成功")
            return self.token

    async def _ensure_token(self):
        """トークンがなければ取得、認証エラー時はリトライ"""
        if not self.token:
            await self.connect()

    async def _request_with_retry(self, method: str, path: str, **kwargs) -> httpx.Response:
        """認証エラー時にトークン再取得してリトライ"""
        await self._ensure_token()
        for attempt in range(3):
            async with httpx.AsyncClient() as client:
                func = getattr(client, method)
                resp = await func(f'{self.base_url}{path}', headers=self._headers(), **kwargs)
            if resp.status_code == 401:
                logger.info(f"[kabu-api] 401応答、トークン再取得 (attempt {attempt + 1}/3)")
                self.token = None
                try:
                    await self.connect()
                except Exception:
                    if attempt < 2:
                        await asyncio.sleep(2)
                        continue
                    raise
                continue
            if resp.status_code >= 400:
                logger.error(f"[kabu-api] {method.upper()} {path} → {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            return resp
        raise httpx.HTTPStatusError("3回リトライ後も認証失敗", request=resp.request, response=resp)

    def _headers(self) -> dict:
        return {'X-API-KEY': self.token or '', 'Host': 'localhost'}

    async def get_balance(self) -> dict:
        """残高照会"""
        resp = await self._request_with_retry('get', '/wallet/cash')
        return resp.json()

    async def get_positions(self) -> list[dict]:
        """保有銘柄照会"""
        resp = await self._request_with_retry('get', '/positions')
        return resp.json()

    async def get_orders(self, product: int = 0) -> list[dict]:
        """注文約定照会。product 0=すべて, 1=現物, 2=信用"""
        resp = await self._request_with_retry('get', '/orders', params={'product': product})
        return resp.json()

    async def send_order(self, code: str, side: str, quantity: int,
                         order_type: str, price: float | None = None,
                         trading_mode: str = 'cash') -> dict:
        """注文送信。trading_mode: cash=現物, margin_system=制度信用, margin_general=一般信用"""
        side_map = {'buy': '2', 'sell': '1'}
        front_order_type_map = {
            'market': '10',   # 成行
            'limit': '20',    # 指値
            'stop': '30',     # 逆指値
        }
        # kabu STATION API: CashMargin 1=現物, 2=新規(信用), 3=返済(信用)
        # 信用取引は新規買付/売建で 2、返済売り/返済買戻しで 3 を指定する仕様
        cash_margin_map = {
            'cash': 1,
            'margin_system': 2,
            'margin_general': 2,
        }
        # 信用区分: kabu STATION では MarginTradeType で指定（1=制度信用6ヶ月, 3=一般信用無期限）
        margin_trade_type_map = {
            'margin_system': 1,
            'margin_general': 3,
        }

        side_code = side_map.get(side, '2')
        cash_margin = cash_margin_map.get(trading_mode, 1)
        order_data = {
            'Password': self.api_password,
            'Symbol': code,  # 銘柄コード（@1不要）
            'Exchange': NEW_ORDER_EXCHANGE,  # 9=SOR（旧 1=東証 は2026-03廃止→Code=100378）
            'SecurityType': 1,  # 株式
            'Side': side_code,
            'CashMargin': cash_margin,
            'DelivType': 2 if (side_code == '2' and trading_mode == 'cash') else 0,
            'FundType': 'AA' if (side_code == '2' and trading_mode == 'cash') else '  ',
            'AccountType': 2,  # 特定
            'Qty': quantity,
            'FrontOrderType': front_order_type_map.get(order_type, '10'),
            'Price': price or 0,
            'ExpireDay': 0,  # 当日
        }
        if trading_mode in margin_trade_type_map:
            order_data['MarginTradeType'] = margin_trade_type_map[trading_mode]

        logger.info(f"[kabu-api] sendorder: {code} {side} {quantity}株 {order_type} price={price} mode={trading_mode}")
        resp = await self._request_with_retry('post', '/sendorder', json=order_data)
        result = resp.json()
        if 'OrderId' in result:
            logger.info(f"[kabu-api] 注文成功: OrderId={result['OrderId']}")
        else:
            logger.error(f"[kabu-api] 注文失敗: Code={result.get('Code')} {result.get('Message')}")
        return result

    async def cancel_order(self, order_id: str) -> dict:
        """注文取消"""
        resp = await self._request_with_retry('put', '/cancelorder', json={
            'OrderId': order_id,
            'Password': self.api_password,
        })
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
            'loginId': result.get('loginId', ''),
            'loginPassword': result.get('loginPassword', ''),
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

    def _get_health(self) -> BrokerageHealth:
        """ヘルス状態を取得（なければ作成）"""
        health = self.db.query(BrokerageHealth).first()
        if not health:
            health = BrokerageHealth(status='unknown', consecutive_failures=0)
            self.db.add(health)
            self.db.commit()
            self.db.refresh(health)
        return health

    def _record_success(self):
        """接続成功を記録"""
        health = self._get_health()
        health.status = 'connected'
        health.consecutive_failures = 0
        health.last_success_at = datetime.now()
        health.last_error_message = None
        self.db.commit()
        logger.info("[broker-health] 接続成功")

    def _record_failure(self, error_message: str):
        """接続失敗を記録"""
        health = self._get_health()
        health.consecutive_failures += 1
        health.last_failure_at = datetime.now()
        health.last_error_message = error_message

        if 'ConnectError' in error_message or '接続できません' in error_message:
            health.status = 'disconnected'
        elif '認証' in error_message or '401' in error_message:
            health.status = 'auth_error'
        else:
            health.status = 'error'

        self.db.commit()
        n = health.consecutive_failures
        logger.error(f"[broker-health] 接続失敗 ({n}回連続): {error_message}")
        if n >= 3:
            logger.critical(
                f"[broker-health] kabu STATION {n}回連続接続失敗！ "
                f"自動売買が停止しています。状態: {health.status}"
            )

    def get_health(self) -> dict:
        """ヘルス状態をAPIレスポンス用に返す"""
        health = self._get_health()
        return {
            'status': health.status,
            'consecutiveFailures': health.consecutive_failures,
            'lastSuccessAt': health.last_success_at.isoformat() if health.last_success_at else None,
            'lastFailureAt': health.last_failure_at.isoformat() if health.last_failure_at else None,
            'lastErrorMessage': health.last_error_message,
        }

    def _restart_kabu_station(self) -> bool:
        """WSLからWindows側のkabu STATIONを再起動+自動ログイン"""
        try:
            config = self.get_config()
            login_id = config.get('loginId', '')
            login_password = config.get('loginPassword', '')

            if not login_id or not login_password:
                logger.error("[broker-health] ログインID/パスワードが未設定")
                return False

            logger.info("[broker-health] kabu STATION再起動+自動ログインを試行...")

            result = subprocess.run(
                [POWERSHELL_EXE, '-ExecutionPolicy', 'Bypass', '-File',
                 AUTO_LOGIN_SCRIPT, '-LoginId', login_id, '-LoginPassword', login_password],
                timeout=120, capture_output=True, text=True,
                env={**dict(subprocess.os.environ), 'API_PASSWORD': config.get('apiPassword', '')},
            )
            logger.info(f"[broker-health] 自動ログイン結果: exit={result.returncode}")
            if result.stdout.strip():
                logger.info(f"[broker-health] stdout: {result.stdout.strip()}")
            if result.stderr.strip():
                logger.error(f"[broker-health] stderr: {result.stderr.strip()}")

            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("[broker-health] 自動ログインがタイムアウト（120秒）")
            return False
        except Exception as e:
            logger.error(f"[broker-health] kabu STATION再起動失敗: {e}")
            return False

    async def connect(self, force_restart: bool = False) -> dict:
        """接続テスト。force_restart=Trueの時のみ失敗時にkabu STATIONを再起動する。

        既定では再起動しない（手動診断でログイン中セッションを破壊しないため）。
        """
        client = self._get_client()
        try:
            token = await client.connect()
            self._record_success()
            return {'connected': True, 'message': '接続成功（トークン取得済み）'}
        except httpx.ConnectError:
            msg = 'kabu STATIONに接続できません'
            self._record_failure(msg)
            if force_restart:
                return await self._connect_with_restart()
            return {'connected': False, 'message': f'{msg}（force_restart=trueで再起動可）'}
        except httpx.HTTPStatusError as e:
            msg = f'認証エラー: {e.response.status_code}'
            self._record_failure(msg)
            if e.response.status_code == 401 and force_restart:
                return await self._connect_with_restart()
            return {'connected': False, 'message': msg}
        except Exception as e:
            msg = f'接続エラー: {str(e)}'
            self._record_failure(msg)
            if force_restart:
                return await self._connect_with_restart()
            return {'connected': False, 'message': msg}

    async def _connect_with_restart(self) -> dict:
        """kabu STATIONを再起動して再接続"""
        health = self._get_health()
        if not self._restart_kabu_station():
            return {'connected': False, 'message': 'kabu STATION再起動に失敗しました'}

        # 再起動後、最大3回リトライ
        client = self._get_client()
        for attempt in range(3):
            try:
                await asyncio.sleep(10)
                token = await client.connect()
                self._record_success()
                logger.info(f"[broker-health] 再起動後の接続成功 (attempt {attempt + 1})")
                return {'connected': True, 'message': f'kabu STATION再起動後に接続成功'}
            except Exception as e:
                logger.warning(f"[broker-health] 再起動後リトライ {attempt + 1}/3 失敗: {e}")

        msg = 'kabu STATION再起動後も接続失敗。手動でログインが必要な可能性があります'
        self._record_failure(msg)
        return {'connected': False, 'message': msg}

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
            # 売り切った残骸建玉（LeavesQty=0）は保有銘柄ではないので除外。
            # 残すと ProfitLoss=None を返しレスポンス検証(float必須)が落ちる。
            qty = pos.get('LeavesQty') or 0
            if qty == 0:
                continue
            code = pos.get('Symbol', '').split('@')[0] if '@' in pos.get('Symbol', '') else pos.get('Symbol', '')
            stock = self.db.query(Stock).filter(Stock.code == code).first()
            result.append({
                'code': code,
                'name': stock.name if stock else pos.get('SymbolName', f'銘柄{code}'),
                'quantity': qty,
                # kabu /positions の取得単価は 'Price' フィールド（'AveragePrice' は存在しない）。
                # None を返すケースに備え 0 にフォールバック。
                'averagePrice': pos.get('Price') or 0,
                'currentPrice': pos.get('CurrentPrice') or 0,
                'profitLoss': pos.get('ProfitLoss') or 0,
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
                           quantity: int, price: float | None = None,
                           trading_mode: str = 'cash') -> dict:
        """注文を送信。trading_mode: cash=現物 / margin_system=制度信用 / margin_general=一般信用"""
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
            result = await client.send_order(code, side, quantity, order_type, price, trading_mode)

            order.brokerage_order_id = result.get('OrderId')
            order.status = 'submitted'
            self.db.commit()
        except Exception as e:
            order.status = 'failed'
            self.db.commit()
            detail = ''
            if hasattr(e, 'response') and e.response is not None:
                try:
                    detail = e.response.text
                except Exception:
                    pass
            logger.error(f"[brokerage] Order failed for {code}: {e} | detail={detail}")
            raise

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

    @staticmethod
    def _interpret_order_state(bo: dict) -> tuple[str | None, float | None]:
        """kabu の注文オブジェクトから (新ステータス, 約定平均単価) を判定。
        変化が無い/判断できない場合は (None, None) を返す。
        kabu API: State 1待機 2処理中 3処理済 4訂正取消中 5終了 /
        Details[].RecType 8=約定成立"""
        order_qty = float(bo.get('OrderQty') or 0)
        cum_qty = float(bo.get('CumQty') or 0)
        state = bo.get('State')

        # 約定平均単価を執行明細(RecType=8 成立)から算出
        exec_qty = 0.0
        exec_amount = 0.0
        for d in bo.get('Details') or []:
            if d.get('RecType') == 8:  # 成立
                q = float(d.get('Qty') or 0)
                p = float(d.get('Price') or 0)
                exec_qty += q
                exec_amount += q * p
        fill_price = (exec_amount / exec_qty) if exec_qty > 0 else None

        # 全約定 → filled
        if order_qty > 0 and cum_qty >= order_qty:
            return 'filled', fill_price
        # 終了かつ未約定 → cancelled（取消/失効/期限切れ）
        if state == 5 and cum_qty == 0:
            return 'cancelled', None
        # 終了かつ部分約定 → filled 扱い（約定分のみ）
        if state == 5 and cum_qty > 0:
            return 'filled', fill_price
        # それ以外（処理中など）はまだ確定しないので据え置き
        return None, None

    async def sync_orders(self) -> dict:
        """kabu STATION の注文約定状態を取得し brokerage_orders を更新する。
        submitted のまま止まっている注文を filled / cancelled へ反映し、
        約定単価が判明すれば price も実約定値に更新する（収支集計の精度向上）。"""
        pending = self.db.query(BrokerageOrder).filter(
            BrokerageOrder.status == 'submitted',
            BrokerageOrder.brokerage_order_id.isnot(None),
        ).all()
        if not pending:
            return {'message': '同期対象の注文はありません', 'updated': 0}

        client = self._get_client()
        await client.connect()
        broker_orders = await client.get_orders()
        by_id = {str(o.get('ID')): o for o in broker_orders}

        updated = 0
        for order in pending:
            bo = by_id.get(str(order.brokerage_order_id))
            if not bo:
                continue
            new_status, fill_price = self._interpret_order_state(bo)
            if new_status and new_status != order.status:
                order.status = new_status
                if new_status == 'filled' and fill_price:
                    order.price = fill_price
                updated += 1
                logger.info(
                    f"[brokerage] sync: {order.code} order#{order.id} "
                    f"submitted→{new_status} (price={order.price})"
                )
        if updated:
            self.db.commit()
        return {'message': f'{updated}件の注文状態を更新しました', 'updated': updated}
