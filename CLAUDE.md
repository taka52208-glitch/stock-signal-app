# 優良株情報取得ツール

## プロジェクト概要
日本株の株価情報を定期取得し、テクニカル指標に基づいて買い時・売り時シグナルを判定するWebアプリケーション。

## 技術スタック

### フロントエンド
- React 18 + TypeScript 5 + MUI v6
- Vite 5 + React Router v6
- Zustand（状態管理）+ React Query（データ取得）
- Recharts（チャート描画）

### バックエンド
- Python 3.11 + FastAPI
- yfinance（株価データ取得）
- pandas-ta（テクニカル指標計算）
- APScheduler（定期実行）
- SQLAlchemy 2.x（ORM）

### データベース
- PostgreSQL（Neon）

### インフラ
- フロントエンド: Vercel
- バックエンド: Render / Railway

## ポート設定
```
frontend: 3847
backend: 8734
```
※ 複数プロジェクト並行開発のため、一般的でないポートを使用

## 環境変数

### フロントエンド（frontend/.env.local）
```
VITE_API_URL=http://localhost:8734
```
- VITE_* プレフィックス必須（Viteの仕様）
- 設定モジュール: src/config/index.ts（import.meta.env集約）

### バックエンド（backend/.env.local）
```
DATABASE_URL=postgresql://...
CORS_ORIGINS=http://localhost:3847
```
- 設定モジュール: src/config.py（os.environ集約）

### 絶対禁止
- .env, .env.test, .env.development, .env.example は使用しない
- process.env / import.meta.env の直接参照禁止（config経由のみ）

## 命名規則

### ファイル名
- コンポーネント: PascalCase.tsx（例: StockList.tsx）
- その他: camelCase.ts（例: useStocks.ts）

### コード
- 変数/関数: camelCase
- 定数: UPPER_SNAKE_CASE
- 型/インターフェース: PascalCase

## 型定義
- 単一真実源: frontend/src/types/index.ts
- バックエンド: backend/src/types.py
- 変更時はフロントエンド→バックエンドの順序で更新

## コード品質基準
```
行長: 120文字
関数行数: 100行以下
ファイル行数: 700行以下
複雑度: 10以下
```

## ディレクトリ構成
```
優良株情報取得ツール/
├── CLAUDE.md
├── docs/
│   ├── requirements.md
│   └── SCOPE_PROGRESS.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── types/
│   │   └── config/
│   ├── .env.local
│   └── package.json
└── backend/
    ├── src/
    │   ├── routers/
    │   ├── services/
    │   ├── models/
    │   └── config.py
    ├── .env.local
    └── requirements.txt
```

## 銘柄コードフォーマット
- yfinance用: `{4桁コード}.T`（例: 7203.T = トヨタ自動車）
- DB保存用: 4桁コードのみ（例: 7203）

## シグナル判定ロジック

### 買いシグナル
- RSI ≤ 30（売られすぎ）
- ゴールデンクロス（短期MA > 中期MA に転換）
- MACD > シグナルライン に転換

### 売りシグナル
- RSI ≥ 70（買われすぎ）
- デッドクロス（短期MA < 中期MA に転換）
- MACD < シグナルライン に転換

## 定期更新スケジュール
- 取引時間中 1時間ごと: 09:30 / 10:30 / 11:30 / 12:30 / 13:30 / 14:30 / 15:30（平日のみ）

## 注意事項

### yfinance
- 非公式APIのため、将来的に仕様変更の可能性あり
- 日本株コードは `.T` サフィックスが必要
- Rate Limitに注意（連続リクエストは1秒以上間隔を空ける）

### テクニカル指標計算
- pandas-taを使用
- RSI: デフォルト14日
- MACD: 短期12日、長期26日、シグナル9日
- 移動平均: 5日（短期）、25日（中期）、75日（長期）
