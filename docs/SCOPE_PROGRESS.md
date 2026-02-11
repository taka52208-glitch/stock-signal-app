# スコープ進捗管理

## フェーズ進捗

- [x] Phase 1: 要件定義
- [x] Phase 2: Git管理
- [x] Phase 3: フロントエンド基盤
- [x] Phase 4: バックエンド基盤
- [x] Phase 5: 機能実装
- [ ] Phase 6: テスト・デプロイ（デプロイ済み、テスト未実装）
- [x] Phase 7: アラート機能
- [x] Phase 8: リスク管理機能
- [x] Phase 9: バックテスト機能
- [x] Phase 10: 証券会社API連携（kabu STATION）
- [x] Phase 11: 自動売買機能（ドライランモード対応）
- [x] Phase 12: インフラ常時稼働化

---

## ページ管理表

| ID | ページ名 | ルート | 権限 | 着手 | 完了 |
|----|----------|--------|------|------|------|
| P-001 | おすすめ銘柄（トップ） | `/` | 全員 | [x] | [x] |
| P-002 | 全銘柄シグナル一覧 | `/signals` | 全員 | [x] | [x] |
| P-003 | 銘柄詳細 | `/stock/:code` | 全員 | [x] | [x] |
| P-004 | 設定 | `/settings` | 全員 | [x] | [x] |
| P-005 | ポートフォリオ | `/portfolio` | 全員 | [x] | [x] |
| P-006 | 取引履歴 | `/history` | 全員 | [x] | [x] |
| P-007 | アラート管理 | `/alerts` | 全員 | [x] | [x] |
| P-008 | リスク管理 | `/risk` | 全員 | [x] | [x] |
| P-009 | バックテスト | `/backtests` | 全員 | [x] | [x] |
| P-010 | 証券会社連携 | `/brokerage` | 全員 | [x] | [x] |
| P-011 | 自動売買設定 | `/auto-trade` | 全員 | [x] | [x] |

---

## API エンドポイント管理表

| メソッド | エンドポイント | 説明 | 着手 | 完了 |
|----------|---------------|------|------|------|
| GET | `/api/health` | ヘルスチェック | [x] | [x] |
| GET | `/api/recommendations` | おすすめ銘柄取得 | [x] | [x] |
| GET | `/api/stocks` | 監視銘柄一覧取得 | [x] | [x] |
| POST | `/api/stocks` | 銘柄追加 | [x] | [x] |
| DELETE | `/api/stocks/{code}` | 銘柄削除 | [x] | [x] |
| GET | `/api/stocks/{code}` | 銘柄詳細取得 | [x] | [x] |
| GET | `/api/stocks/{code}/chart` | チャートデータ取得 | [x] | [x] |
| GET | `/api/settings` | 設定取得 | [x] | [x] |
| PUT | `/api/settings` | 設定更新 | [x] | [x] |
| GET | `/api/settings/tunnel-url` | トンネルURL取得 | [x] | [x] |
| PUT | `/api/settings/tunnel-url` | トンネルURL更新 | [x] | [x] |
| POST | `/api/update` | 手動データ更新トリガー | [x] | [x] |
| GET | `/api/transactions` | 取引一覧取得 | [x] | [x] |
| POST | `/api/transactions` | 取引追加 | [x] | [x] |
| DELETE | `/api/transactions/{id}` | 取引削除 | [x] | [x] |
| GET | `/api/portfolio` | ポートフォリオ取得 | [x] | [x] |
| GET | `/api/alerts` | アラート一覧取得 | [x] | [x] |
| POST | `/api/alerts` | アラート作成 | [x] | [x] |
| DELETE | `/api/alerts/{id}` | アラート削除 | [x] | [x] |
| GET | `/api/alerts/history` | アラート履歴取得 | [x] | [x] |
| POST | `/api/alerts/mark-read` | アラート既読 | [x] | [x] |
| GET | `/api/alerts/unread-count` | 未読アラート数取得 | [x] | [x] |
| GET | `/api/risk/rules` | リスクルール取得 | [x] | [x] |
| PUT | `/api/risk/rules` | リスクルール更新 | [x] | [x] |
| POST | `/api/risk/evaluate-trade` | 取引リスク評価 | [x] | [x] |
| GET | `/api/risk/checklist/{code}` | チェックリスト取得 | [x] | [x] |
| GET | `/api/risk/suggest-prices/{code}` | 価格提案取得 | [x] | [x] |
| GET | `/api/backtests` | バックテスト一覧 | [x] | [x] |
| POST | `/api/backtests` | バックテスト作成 | [x] | [x] |
| GET | `/api/backtests/{id}` | バックテスト詳細 | [x] | [x] |
| DELETE | `/api/backtests/{id}` | バックテスト削除 | [x] | [x] |
| GET | `/api/backtests/{id}/trades` | バックテスト取引一覧 | [x] | [x] |
| GET | `/api/backtests/{id}/snapshots` | バックテストスナップショット | [x] | [x] |
| POST | `/api/backtests/compare` | バックテスト比較 | [x] | [x] |
| GET | `/api/brokerage/config` | 証券会社設定取得 | [x] | [x] |
| PUT | `/api/brokerage/config` | 証券会社設定更新 | [x] | [x] |
| POST | `/api/brokerage/connect` | 証券会社接続テスト | [x] | [x] |
| GET | `/api/brokerage/balance` | 残高照会 | [x] | [x] |
| GET | `/api/brokerage/positions` | 保有銘柄照会 | [x] | [x] |
| GET | `/api/brokerage/orders` | 注文一覧取得 | [x] | [x] |
| POST | `/api/brokerage/orders` | 注文送信 | [x] | [x] |
| DELETE | `/api/brokerage/orders/{id}` | 注文キャンセル | [x] | [x] |
| POST | `/api/brokerage/sync` | ポジション同期 | [x] | [x] |
| GET | `/api/auto-trade/config` | 自動売買設定取得 | [x] | [x] |
| PUT | `/api/auto-trade/config` | 自動売買設定更新 | [x] | [x] |
| POST | `/api/auto-trade/toggle` | 自動売買ON/OFF | [x] | [x] |
| GET | `/api/auto-trade/log` | 自動売買ログ取得 | [x] | [x] |
| GET | `/api/auto-trade/stocks` | 自動売買銘柄一覧 | [x] | [x] |
| PUT | `/api/auto-trade/stocks/{code}` | 自動売買銘柄設定 | [x] | [x] |

---

## 成果物チェックリスト

### ドキュメント
- [x] `docs/requirements.md` - 要件定義書
- [x] `docs/SCOPE_PROGRESS.md` - 進捗管理表
- [x] `docs/DEPLOYMENT.md` - デプロイ手順書
- [x] `CLAUDE.md` - プロジェクト設定

### フロントエンド
- [x] `frontend/` - Reactアプリケーション
- [x] おすすめ銘柄ページ（買い/売り推奨・投資予算設定・購入提案）
- [x] 全銘柄シグナル一覧ページ（シグナル表示・銘柄追加/削除・シグナル強度）
- [x] 銘柄詳細ページ（チャート・RSI・MACD・移動平均線・売買目安カード）
- [x] 設定ページ（RSI閾値・移動平均期間・投資予算）
- [x] ポートフォリオページ（保有銘柄・損益計算）
- [x] 取引履歴ページ（売買記録・削除）
- [x] アラート管理ページ（価格・シグナル・RSIアラート・通知履歴）
- [x] リスク管理ページ（リスクルール・取引評価・チェックリスト・価格提案）
- [x] バックテストページ（戦略シミュレーション・比較分析）
- [x] 証券会社連携ページ（kabu STATION接続・残高・ポジション・注文）
- [x] 自動売買設定ページ（ドライランモード・銘柄別設定・実行ログ）
- [x] APIクライアント（`src/api/client.ts` - Render/トンネルデュアルモード対応）
- [x] 型定義（`src/types/index.ts`）
- [x] 設定モジュール（`src/config/index.ts`）
- [ ] カスタムフック（`src/hooks/` - 空）
- [x] 共通コンポーネント（SignalStrengthDisplay, BuyRecommendationCard, SellRecommendationCard, BudgetSetting, AlertBadge, PriceSuggestionCard）

### バックエンド
- [x] `backend/` - FastAPIアプリケーション
- [x] データベースモデル（Stock, StockPrice, Signal, Setting, Transaction, Alert, AlertHistory, RiskRule, Backtest, BacktestTrade, BacktestSnapshot, BrokerageConfig, BrokerageOrder, AutoTradeConfig, AutoTradeStock, AutoTradeLog）
- [x] 株価取得サービス（yfinance + モックモード対応）
- [x] テクニカル指標計算（RSI, MACD, SMA）
- [x] シグナル判定ロジック（買い/売り/様子見）
- [x] シグナル詳細計算（強度・目標価格・損切りライン・支持線/抵抗線）
- [x] おすすめ銘柄ロジック（投資予算配分・購入株数・期待利益計算）
- [x] アラートサービス（価格・シグナル・RSI条件監視）
- [x] リスク管理サービス（ルール評価・チェックリスト・価格提案）
- [x] バックテストサービス（戦略シミュレーション・スナップショット・比較）
- [x] 証券会社連携サービス（kabu STATION API・注文・残高・ポジション）
- [x] 自動売買サービス（シグナル連動・ドライラン・保守的フィルター）
- [x] 定期更新スケジューラ（09:30 / 12:30 / 15:30 + アラート・自動売買連動）
- [x] CORS設定（Vercelサブドメイン正規表現対応）
- [x] グレースフルシャットダウン（SIGTERM対応）
- [ ] Rate Limit（未実装）
- [x] 簡易マイグレーション（起動時ALTER TABLEによる列追加）
- [ ] データベースマイグレーション（Alembic未導入、`create_all`+ALTER TABLEで代用）

### インフラ・デプロイ
- [x] フロントエンド: Vercel（`vercel.json` + `kabu-signal-navi.vercel.app`）
- [x] バックエンド（常時稼働）: Render（`render.yaml` + `stock-signal-api-u9al.onrender.com`）
- [x] バックエンド（ローカル）: cloudflaredトンネル経由（証券会社API連携用）
- [x] DB: Neon PostgreSQL（常時稼働）
- [x] PC起動時自動起動（Windowsタスクスケジューラ → WSL → crontab @reboot）
- [x] 起動スクリプト（`start.sh` - バックエンド+トンネル一括起動・URL自動登録）
- [ ] CI/CDパイプライン（未構築）

### テスト
- [ ] フロントエンドテスト（未実装）
- [ ] バックエンドテスト（未実装）

---

## 未対応項目まとめ

| 項目 | 優先度 | 備考 |
|------|--------|------|
| テスト実装（フロント/バック） | 中 | テストフレームワーク未導入 |
| Rate Limit | 中 | 要件定義では1分60リクエスト |
| Alembicマイグレーション | 低 | 現状`create_all`+ALTER TABLEで動作中 |
| CI/CDパイプライン | 低 | 現状は手動デプロイ |
| カスタムフック分離 | 低 | 現状はページ内にインライン |
| Cloudflare Named Tunnel | 低 | 現状Quick Tunnel（URL変動）で運用中。ドメイン取得で固定URL化可能 |
