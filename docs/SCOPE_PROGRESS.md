# スコープ進捗管理

## フェーズ進捗

- [x] Phase 1: 要件定義
- [x] Phase 2: Git管理
- [x] Phase 3: フロントエンド基盤
- [x] Phase 4: バックエンド基盤
- [x] Phase 5: 機能実装
- [ ] Phase 6: テスト・デプロイ（デプロイ済み、テスト未実装）

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
| POST | `/api/update` | 手動データ更新トリガー | [x] | [x] |
| GET | `/api/transactions` | 取引一覧取得 | [x] | [x] |
| POST | `/api/transactions` | 取引追加 | [x] | [x] |
| DELETE | `/api/transactions/{id}` | 取引削除 | [x] | [x] |
| GET | `/api/portfolio` | ポートフォリオ取得 | [x] | [x] |

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
- [x] APIクライアント（`src/api/client.ts`）
- [x] 型定義（`src/types/index.ts`）
- [x] 設定モジュール（`src/config/index.ts`）
- [ ] カスタムフック（`src/hooks/` - 空）
- [x] 共通コンポーネント（SignalStrengthDisplay, BuyRecommendationCard, SellRecommendationCard, BudgetSetting）

### バックエンド
- [x] `backend/` - FastAPIアプリケーション
- [x] データベースモデル（Stock, StockPrice, Signal, Setting, Transaction）
- [x] 株価取得サービス（yfinance + モックモード対応）
- [x] テクニカル指標計算（RSI, MACD, SMA）
- [x] シグナル判定ロジック（買い/売り/様子見）
- [x] シグナル詳細計算（強度・目標価格・損切りライン・支持線/抵抗線）
- [x] おすすめ銘柄ロジック（投資予算配分・購入株数・期待利益計算）
- [x] 定期更新スケジューラ（09:30 / 12:30 / 15:30）
- [x] CORS設定
- [x] グレースフルシャットダウン（SIGTERM対応）
- [ ] Rate Limit（未実装）
- [x] 簡易マイグレーション（起動時ALTER TABLEによるSignal列追加）
- [ ] データベースマイグレーション（Alembic未導入、`create_all`+ALTER TABLEで代用）

### デプロイ
- [x] フロントエンド: Vercel（`vercel.json` + デプロイスクリプト）
- [x] バックエンド: Render（`render.yaml` + `runtime.txt`）
- [x] デプロイスクリプト（`scripts/deploy-*.sh`）
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
| Alembicマイグレーション | 低 | 現状`create_all`で動作中 |
| CI/CDパイプライン | 低 | 現状は手動デプロイ |
| カスタムフック分離 | 低 | 現状はページ内にインライン |
| ~~共通コンポーネント分離~~ | ~~低~~ | 済: SignalStrengthDisplay等を追加 |
