from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.database import get_db
from src.models.stock import Transaction, Stock, StockPrice
from src.models.schemas import (
    TransactionRequest,
    TransactionResponse,
    HoldingResponse,
    PortfolioResponse,
)

router = APIRouter(prefix='/api/transactions', tags=['transactions'])

STOCK_NAMES = {
    '7203': 'トヨタ自動車',
    '6758': 'ソニーグループ',
    '9984': 'ソフトバンクグループ',
    '8306': '三菱UFJフィナンシャル・グループ',
    '9432': '日本電信電話',
    '6861': 'キーエンス',
    '7974': '任天堂',
    '4063': '信越化学工業',
    '6098': 'リクルートホールディングス',
    '8035': '東京エレクトロン',
    '6501': '日立製作所',
    '6902': 'デンソー',
    '4568': '第一三共',
    '6920': 'レーザーテック',
    '8058': '三菱商事',
    '9983': 'ファーストリテイリング',
    '4661': 'オリエンタルランド',
    '7741': 'HOYA',
    '6594': 'ニデック',
    '6273': 'SMC',
    '8316': '三井住友フィナンシャルグループ',
    '8411': 'みずほフィナンシャルグループ',
    '8766': '東京海上ホールディングス',
    '6367': 'ダイキン工業',
    '6971': '京セラ',
    '7267': '本田技研工業',
    '7269': 'スズキ',
    '4755': '楽天グループ',
    '9613': 'NTTデータグループ',
    '4689': 'LINEヤフー',
    '8001': '伊藤忠商事',
    '8031': '三井物産',
    '8053': '住友商事',
    '4502': '武田薬品工業',
    '4503': 'アステラス製薬',
    '9433': 'KDDI',
    '9434': 'ソフトバンク',
    '8830': '住友不動産',
    '3289': '東急不動産ホールディングス',
    '2914': '日本たばこ産業',
    '2802': '味の素',
    '9501': '東京電力ホールディングス',
    '4911': '資生堂',
    '4452': '花王',
    '5401': '日本製鉄',
    '5108': 'ブリヂストン',
    '6762': 'TDK',
    '6981': '村田製作所',
    '9766': 'コナミグループ',
    '3659': 'ネクソン',
}


def get_stock_name(db: Session, code: str) -> str:
    stock = db.query(Stock).filter(Stock.code == code).first()
    if stock:
        return stock.name
    return STOCK_NAMES.get(code, f'銘柄{code}')


def get_current_price(db: Session, code: str) -> float:
    price = db.query(StockPrice).filter(
        StockPrice.code == code
    ).order_by(StockPrice.date.desc()).first()
    return price.close if price else 0.0


@router.get('', response_model=list[TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    """取引履歴を取得"""
    transactions = db.query(Transaction).order_by(Transaction.transaction_date.desc()).all()
    result = []
    for t in transactions:
        result.append({
            'id': t.id,
            'code': t.code,
            'name': get_stock_name(db, t.code),
            'transactionType': t.transaction_type,
            'quantity': t.quantity,
            'price': t.price,
            'totalAmount': t.quantity * t.price,
            'transactionDate': t.transaction_date.isoformat() if t.transaction_date else '',
            'memo': t.memo,
        })
    return result


@router.post('', response_model=TransactionResponse)
def add_transaction(request: TransactionRequest, db: Session = Depends(get_db)):
    """取引を記録"""
    transaction = Transaction(
        code=request.code,
        transaction_type=request.transactionType,
        quantity=request.quantity,
        price=request.price,
        memo=request.memo,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        'id': transaction.id,
        'code': transaction.code,
        'name': get_stock_name(db, transaction.code),
        'transactionType': transaction.transaction_type,
        'quantity': transaction.quantity,
        'price': transaction.price,
        'totalAmount': transaction.quantity * transaction.price,
        'transactionDate': transaction.transaction_date.isoformat() if transaction.transaction_date else '',
        'memo': transaction.memo,
    }


@router.delete('/{transaction_id}')
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """取引を削除"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail='取引が見つかりません')
    db.delete(transaction)
    db.commit()
    return {'message': '削除しました'}


@router.get('/portfolio', response_model=PortfolioResponse)
def get_portfolio(db: Session = Depends(get_db)):
    """ポートフォリオ（保有株一覧）を取得"""
    transactions = db.query(Transaction).all()

    # 銘柄ごとに集計
    holdings_data = {}
    for t in transactions:
        if t.code not in holdings_data:
            holdings_data[t.code] = {'buy_quantity': 0, 'buy_total': 0, 'sell_quantity': 0}

        if t.transaction_type == 'buy':
            holdings_data[t.code]['buy_quantity'] += t.quantity
            holdings_data[t.code]['buy_total'] += t.quantity * t.price
        else:  # sell
            holdings_data[t.code]['sell_quantity'] += t.quantity

    # 保有株リスト作成
    holdings = []
    total_cost = 0
    total_value = 0

    for code, data in holdings_data.items():
        quantity = data['buy_quantity'] - data['sell_quantity']
        if quantity <= 0:
            continue

        avg_price = data['buy_total'] / data['buy_quantity'] if data['buy_quantity'] > 0 else 0
        current_price = get_current_price(db, code)
        cost = quantity * avg_price
        value = quantity * current_price
        profit_loss = value - cost
        profit_loss_percent = (profit_loss / cost * 100) if cost > 0 else 0

        holdings.append({
            'code': code,
            'name': get_stock_name(db, code),
            'quantity': quantity,
            'averagePrice': round(avg_price, 2),
            'currentPrice': round(current_price, 2),
            'totalCost': round(cost, 2),
            'currentValue': round(value, 2),
            'profitLoss': round(profit_loss, 2),
            'profitLossPercent': round(profit_loss_percent, 2),
        })

        total_cost += cost
        total_value += value

    total_profit_loss = total_value - total_cost
    total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0

    return {
        'holdings': holdings,
        'totalCost': round(total_cost, 2),
        'totalValue': round(total_value, 2),
        'totalProfitLoss': round(total_profit_loss, 2),
        'totalProfitLossPercent': round(total_profit_loss_percent, 2),
    }
