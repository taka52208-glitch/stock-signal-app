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
- [x] Phase 13: 自動売買ログ・安定性改善
- [x] Phase 14: ドライラン収支表示（実現/含み損益）
- [x] Phase 15: 自動売買安定化・本番環境バグ修正
- [x] Phase 16: シグナルロジック強化（収益性向上）
- [x] Phase 17: シグナル取引頻度改善
- [x] Phase 18: 自動売買の実行信頼性強化
- [x] Phase 19: ドライラン自動売買の実用性改善
- [x] Phase 20: ドライラン投入金額・利益改善
- [x] Phase 21: 自動売買取引頻度の大幅改善
- [x] Phase 22: 勝率・利益率改善（実資金投入準備）
- [x] Phase 23: 投入金額対比利益率の大幅改善
- [x] Phase 24: 取引頻度改善（リスク緩和・シグナル強度閾値修正）

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
| GET | `/api/auto-trade/virtual-portfolio` | ドライラン仮想収支 | [x] | [x] |
| POST | `/api/auto-trade/run` | 自動売買手動実行 | [x] | [x] |

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
- [x] 自動売買設定ページ（ドライランモード・銘柄別設定・実行ログ・仮想収支表示・通常API経由）
- [x] APIクライアント（`src/api/client.ts` - Render/トンネルデュアルモード対応、自動売買は通常API）
- [x] 型定義（`src/types/index.ts`）
- [x] 設定モジュール（`src/config/index.ts`）
- [ ] カスタムフック（`src/hooks/` - 空）
- [x] 共通コンポーネント（SignalStrengthDisplay, BuyRecommendationCard, SellRecommendationCard, BudgetSetting, AlertBadge, PriceSuggestionCard）

### バックエンド
- [x] `backend/` - FastAPIアプリケーション
- [x] データベースモデル（Stock, StockPrice, Signal, Setting, Transaction, Alert, AlertHistory, RiskRule, Backtest, BacktestTrade, BacktestSnapshot, BrokerageConfig, BrokerageOrder, AutoTradeConfig, AutoTradeStock, AutoTradeLog）
- [x] 株価取得サービス（yfinance + モックモード対応）
- [x] テクニカル指標計算（RSI, MACD, SMA, BB, ATR, 出来高比率, Stochastic, Williams%R, ADX）
- [x] シグナル判定ロジック（加重スコアリング・ADX相場状態判定・確認待ち2日・BB/出来高確認・RSIモメンタム・MACDヒストグラム・価格MA25クロス・Stoch/WillRクロス・出来高フィルター強化）
- [x] シグナル詳細計算（強度・目標価格・ATR動的損切り・支持線/抵抗線）
- [x] おすすめ銘柄ロジック（投資予算配分・購入株数・期待利益計算）
- [x] アラートサービス（価格・シグナル・RSI条件監視）
- [x] リスク管理サービス（ルール評価・チェックリスト・価格提案）
- [x] バックテストサービス（戦略シミュレーション・スナップショット・比較）
- [x] 証券会社連携サービス（kabu STATION API・注文・残高・ポジション）
- [x] 自動売買サービス（シグナル連動・ドライラン・ATR動的損切り/利確・3段階利確・トレーリングストップ・時間帯重み・昼休み実行禁止・全ケースログ記録・実現/含み損益計算・重複買い防止・ドライラン仮想ポートフォリオ対応リスク評価）
- [x] 定期更新スケジューラ（09:30〜15:30の30分ごと + アラート・自動売買連動 + watchdog復帰対策）
- [x] CORS設定（Vercelサブドメイン正規表現対応）
- [x] グレースフルシャットダウン（SIGTERM対応）
- [ ] Rate Limit（未実装）
- [x] 簡易マイグレーション（起動時ALTER TABLEによる列追加・エラーログ・検証付き）
- [ ] データベースマイグレーション（Alembic未導入、`create_all`+ALTER TABLEで代用）

### インフラ・デプロイ
- [x] フロントエンド: Vercel（`vercel.json` + `kabu-signal-navi.vercel.app`）
- [x] バックエンド（常時稼働）: Render（`render.yaml` + `stock-signal-api-u9al.onrender.com`）
- [x] バックエンド（ローカル）: cloudflaredトンネル経由（証券会社API連携用）
- [x] DB: Neon PostgreSQL（常時稼働）
- [x] PC起動時自動起動（systemd + WSL自動起動）
- [x] 起動スクリプト（`start.sh` - バックエンド+トンネル一括起動・URL自動登録・バイナリログ対応）
- [x] WSLスリープ復帰対策（5分間隔watchdog + 起動時キャッチアップ）
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
| バックエンドプロセス監視 | ~~中~~ 済 | ~~start.shでuvicornが落ちても再起動されない~~ watchdog実装済み |
| ~~investmentBudget増額~~ | ~~低~~ 済 | ~~現在50,000円~~ Phase 20で1,000,000円に増額済み |

---

## Phase 15: 自動売買安定化・本番環境バグ修正（2026-02-23）

### 対応内容
1. **ポート競合解消**: 電子書籍ツール（8734→8735）とのポート競合を解消、プロセス整理
2. **モックモード修正**: `MOCK_MODE`デフォルトを`true`→`false`に変更。Render環境でランダム価格による誤った損切りが発生していた
3. **自動売買デフォルト設定修正**: バックエンド/フロントエンド両方の`DEFAULT_CONFIG`を統一（enabled=true, minSignalStrength=1）
4. **手動実行エンドポイント追加**: `POST /api/auto-trade/run`（ロックバイパス付き）
5. **仮想収支リセット**: モックデータによる架空損益（-24,329円）をクリア
6. **Vercel環境変数修正**: `VITE_API_URL`の改行文字混入を修正・再デプロイ

---

## Phase 16: シグナルロジック強化・収益性向上（2026-02-24）

### 対応内容
1. **テクニカル指標追加**: ボリンジャーバンド（20日/2σ）、ATR（14日）、出来高比率（20日平均比）をSignalモデルに追加
2. **加重スコアリング**: RSI(1.0), MACD(1.5), MAクロス(1.0), BBバウンス/タッチ(0.5), 出来高確認(0.5), トレンド整合(0.5) の加重スコア方式に変更。signal_score(0.0-5.0)として保存
3. **トレンドフィルター**: 価格<SMA75で買い抑制、価格>SMA75で売り抑制。下降トレンドでの買いシグナルを排除
4. **BBシグナル**: BB下限バウンス→買い、BB上限タッチ→売り（前日の抜けから当日の反転を確認）
5. **出来高確認**: volume_ratio >= 1.5の場合に確認加点（単独ではシグナルにならない）
6. **ATR動的損切り/利確**: 買いシグナル時 目標=entry+4*ATR, 損切り=entry-2.5*ATR（ATR未取得時は従来の固定%にフォールバック）※Phase 20で倍率変更
7. **トレーリングストップ**: 含み益>=2*ATRでトレーリングストップ発動、含み益>=1*ATRでブレークイーブンストップ
8. **フロントエンド型拡張**: StockDetail/ChartDataにBB/ATR/volumeRatio/signalScore追加

### 期待効果
- トレンドフィルターで偽シグナル30-50%削減
- 出来高確認で低確信度エントリー排除
- ATR動的損切りでボラティリティに応じた適応的リスク管理
- トレーリングストップで勝ちトレードの利益最大化

---

## Phase 17: シグナル取引頻度改善（2026-02-25）

### 背景
- 直近5日間のシグナル分布が hold=77.5%, buy=10%, sell=12.5% と取引シグナルが極端に少ない
- 主原因: トレンドフィルターによるシグナル全消去、クロスオーバー系の厳しすぎる条件

### 対応内容
1. **トレンドフィルター緩和**: シグナル全消去 → スコア×0.3ペナルティ乗算 + `CounterTrend`タグ付与。逆トレンドでもRSI+MACD複合なら strength=1 で検出可能に
2. **RSIモメンタムゾーン追加**: RSI 35-45かつ上昇中→`RSI_Rising`(0.5)、RSI 55-65かつ下落中→`RSI_Falling`(0.5)。従来のRSI≤30/≥70に加え中間域の方向性も検出
3. **MACDヒストグラム反転追加**: ヒストグラム負→正→`MACD_Hist`(0.8)、正→負→`MACD_Hist`(0.8)。MACDクロスと排他で重複加点なし
4. **価格-MA25クロス追加**: 終値がSMA25を上抜け→`PriceAboveMA25`(0.5)、下抜け→`PriceBelowMA25`(0.5)。GoldenCross/DeadCrossと排他
5. **DBマイグレーション**: active_signals列幅 VARCHAR(100)→VARCHAR(200) に拡張
6. **フロントエンドシグナルラベル**: BuyRecommendationCard/SellRecommendationCardに全10種のシグナルラベルを追加
7. **マイグレーション堅牢化**: `except: pass`廃止→エラー種別判定・ログ出力・rollback追加。起動時に必須列の存在を検証しCRITICALログ出力

### 初回実行結果（2/25）
- buy: 2銘柄 (6098 RSI, 7741 MACD)、sell: 2銘柄 (8058 RSI, 6273 RSI)、hold: 16銘柄
- 新シグナル（RSI_Rising, MACD_Hist, PriceAboveMA25等）は当日の市場状況では未発火。数日間の運用で効果検証予定

---

## Phase 18: 自動売買の実行信頼性強化（2026-02-26）

### 対応内容
1. **systemdサービス化**: `stock-signal-backend.service`（Restart=always, enabled）で常時稼働を保証
2. **旧サービス整理**: `kabu-signal.service`（system/user両方）とcrontab `@reboot start-daemon.sh` を停止・削除
3. **ファイルログ追加**: `backend/logs/backend.log`（TimedRotatingFileHandler, 日次30日保持）
4. **キャッチアップ強化**: `_auto_trade_not_run_today()` で auto_trade_log の有無もチェック
5. **watchdog拡張**: lifespan + watchdog_check 両方で stale data/no auto-trade logs 条件に拡張

---

## Phase 19: ドライラン自動売買の実用性改善（2026-02-26）

### 背景
4日間のドライラン実績分析で3つの構造的問題を発見:
- 同一銘柄（6098）を4回重複購入（ポジション確認なし）
- ATR損切り距離 > 5% で大半がリスクブロック（2/26は7件中5件）
- 非保有株の売りシグナルログが冗長

### 対応内容
1. **重複買い防止**: buy処理冒頭で既存保有チェック。保有中なら `skipped`（「既に保有中（N株）」）でスキップ
2. **ドライラン対応リスク評価**: `evaluate_trade()` に `dry_run` パラメータ追加。ドライラン時は `auto_trade_log` から仮想ポートフォリオを計算し `maxOpenPositions` が正しく機能
3. **maxLossPerTrade 緩和**: デフォルト 5% → 10%。ATR損切り（entry - 2*ATR）の通常距離 5-10% に適合
4. **非保有売りのログ軽減**: logger出力を `info` → `debug` に変更（DBログは維持）

### 変更ファイル
- `backend/src/services/auto_trade_service.py` — 修正1, 2, 4
- `backend/src/services/risk_service.py` — 修正2, 3（`_get_real_holdings()` / `_get_dry_run_holdings()` ヘルパー追加）

### 期待効果
- 同一銘柄の重複購入が解消（1銘柄1ポジション）
- risk_blocked率の大幅減少（5%→10%閾値で大半のATR損切りが通過）
- ドライランでもmaxOpenPositions（5銘柄上限）が正しく適用
- ログのS/N比向上（非保有売りのノイズ除去）

---

## Phase 20: ドライラン投入金額・利益改善（2026-02-27）

### 背景
- ドライラン投資予算が5万円（1銘柄1万円）と少なすぎ、高価格帯銘柄が購入不可
- 利確が早すぎ（5%/無条件7.5%）で大きなトレンドを取れない
- 1日5回の取引上限で機会損失

### 対応内容
1. **投資予算増額**: 50,000円 → 1,000,000円（DBマイグレーション付き）
2. **予算計算ロジック改善**: 固定 `/5` → `/ maxOpenPositions` に連動（設定変更時に自動追従）
3. **最大保有銘柄数増加**: 5 → 10（1銘柄あたり10万円で分散投資拡大）
4. **1日最大取引数増加**: 5 → 15（取引チャンス増加）
5. **利確閾値改善**: takeProfitPercent 5.0% → 8.0%、無条件利確 1.5倍(7.5%) → 2.0倍(16%)
6. **損切り閾値改善**: stopLossPercent -3.0% → -5.0%（ノイズで切られにくく）
7. **ATR利確倍率変更**: entry + 3*ATR → entry + 4*ATR（大きなトレンド捕捉）
8. **ATR損切り倍率変更**: entry - 2*ATR → entry - 2.5*ATR（余裕を持たせた損切り）
9. **Signal保存値の整合**: stock_service.py の target_price/stop_loss_price を新ATR倍率に統一
10. **DBマイグレーション**: main.py lifespan で旧デフォルト値のみ条件付きUPDATE（冪等・カスタム値保持）
11. **フロントエンド更新**: maxTradesPerDay スライダー max=10→20、デフォルト値をバックエンドと統一

### 変更ファイル
- `backend/src/config.py` — 修正1
- `backend/src/services/auto_trade_service.py` — 修正2, 4, 5, 6, 7, 8
- `backend/src/services/risk_service.py` — 修正3
- `backend/src/services/stock_service.py` — 修正9
- `backend/src/main.py` — 修正10
- `frontend/src/pages/AutoTradeSettings.tsx` — 修正11

### 期待効果
- 1銘柄あたり投入額10万円で高価格帯銘柄も購入可能
- 最大10銘柄×10万円 = 100万円のフル活用
- 利確幅拡大でトレンド追従型の利益向上
- ATR 4倍利確で大幅な値上がりを捕捉

---

## Phase 21: 自動売買取引頻度の大幅改善（2026-03-03）

### 背景
- 50銘柄中わずかしかシグナルが出ず、取引機会が限定的
- ストキャスティクス/ウィリアムズ%Rなど追加指標で極値判定を強化したい

### 対応内容
1. **監視銘柄拡大**: 20 → 50銘柄（日経225主要銘柄追加）
2. **新テクニカル指標**: Stochastic(%K/%D, k=14,d=3), Williams%R(length=14)
3. **新シグナル**: Stoch_GC(1.0,買), Stoch_DC(1.0,売), WillR_Buy(0.5,買), WillR_Sell(0.5,売)
4. **RSI閾値緩和**: 買い35→40, 売り65→60
5. **重み変更**: RSI_Rising/Falling 0.5→0.7, MACD_Hist 0.8→1.0, BB_Bounce/Touch 0.5→0.8
6. **strength閾値緩和**: >=3.0→3,>=1.5→2 を >=2.5→3,>=1.0→2 に
7. **トレンドペナルティ緩和**: 0.3→0.5
8. **スケジュール高頻度化**: 1時間→30分間隔（7→12回/日）
9. **銘柄自動登録**: main.py lifespan で未登録銘柄をバルクINSERT + AutoTradeStock有効化

---

## Phase 22: 勝率・利益率改善 — 実資金投入準備（2026-03-04）

### 背景
- 実際の資金投入に向けて、ドライランの勝率と利益率をさらに改善したい
- 現状のリスクリワード比が1:1.6と低く、ダマシシグナルでの損失が課題

### 対応内容
1. **リスクリワード比1:2に改善**: ATR利確 4→5×ATR、フォールバック利確 8→10%。損切りは据え置き2.5×ATR/-5%
2. **シグナル確認待ち（次足確認）**: MACD/GoldenCross/DeadCross/Stochクロス系で3日間確認。2日前に未クロス→前日クロス→今日維持の場合のみ有効。ダマシを大幅排除
3. **出来高重み強化**: VolConfirm 0.5→1.0に倍増。出来高不足（volume_ratio < 0.8）時はスコア×0.5ペナルティ + 'LowVolume'タグ
4. **時間帯重み付けフィルター**: 寄付き後（9:30）×1.2、昼休み前後（11:00-12:30）×0.6-0.8、大引け前（14:30）×1.1。シグナルスコアに乗算して強度を再計算
5. **段階的イグジット（部分利確）**: 含み益≥3×ATRで保有量の50%を利確、残りはトレーリングストップで追従。全量一括決済から段階的決済に改善
6. **minSignalStrength引き上げ**: 1→2にデフォルト変更。弱いシグナル（strength=1）での取引を排除して勝率向上

### 変更ファイル
- `backend/src/services/stock_service.py` — 修正1, 2, 3（確認待ち・出来高強化・ATR倍率）
- `backend/src/services/auto_trade_service.py` — 修正1, 4, 5, 6（時間帯フィルター・段階的イグジット・デフォルト値）
- `backend/src/main.py` — 修正6（Phase 22 DBマイグレーション）
- `frontend/src/pages/AutoTradeSettings.tsx` — 修正6（フロントエンドデフォルト値同期）

### 期待効果
- 確認待ちでクロス系ダマシを50%以上削減
- 出来高フィルターで低信頼シグナルを排除
- 時間帯重みで昼休み前後の低品質シグナルを抑制
- R/R比1:2で1トレードあたりの期待値が大幅改善
- 段階的利確で利益の取りこぼしを削減
- minSignalStrength=2で勝率向上

---

## Phase 23: 投入金額対比利益率の大幅改善（2026-03-05）

### 背景
- 投入金額100万円に対して利益率が低い
- 相場状態（トレンド/レンジ）を判定せず全シグナルを同等に扱っていたためダマシが多い
- 10銘柄分散で1銘柄あたりの投資額が小さく利益額も小さい

### 対応内容
1. **ADX指標の導入（相場状態判定）**: ADX(14)を計算し、ADX>25→強トレンド（トレンドフォロー重視、逆張り×0.3）、ADX<20→レンジ相場（トレンドフォロー×0.5）、ADX20-25→従来ペナルティ。新タグ: StrongTrend, RangeMarket
2. **段階的利確の3段階化**: 旧: 3×ATRで50%利確のみ → 新: 2.5×ATR(33%), 3.5×ATR(33%), 5×ATR(全量)。第1段階利確後はブレイクイーブンストップに移行
3. **ポジション集中投資**: maxOpenPositions 10→5に変更。1銘柄あたり投入額10万円→20万円に倍増
4. **シグナル確認待ち短縮**: 3日→2日に短縮（MACD/GoldenCross/DeadCross/Stochastic全て）。prev2参照を完全除去、最小データ数3→2
5. **出来高フィルター強化**: volume_ratio<0.7→シグナル除外(score=0)、<0.8→×0.5ペナルティ、>=1.5→+1.0ボーナス、>=2.0→+1.5ボーナス（ブレイクアウト確認）
6. **時間帯重み調整**: 11:30/12:00→0.0（実行禁止）、10:00→1.2、14:00/14:30→1.2（信頼性高い時間帯ボーナス）

### 変更ファイル
- `backend/src/models/stock.py` — Signal model に adx カラム追加
- `backend/src/services/stock_service.py` — ADX計算・ADXベース相場判定・確認待ち2日化・出来高フィルター強化
- `backend/src/services/auto_trade_service.py` — 3段階利確・時間帯重み調整
- `backend/src/services/risk_service.py` — maxOpenPositions 10→5
- `backend/src/main.py` — Phase 23 DBマイグレーション（adxカラム追加・maxOpenPositions更新）
- `frontend/src/components/BuyRecommendationCard.tsx` — 新シグナルラベル追加
- `frontend/src/components/SellRecommendationCard.tsx` — 新シグナルラベル追加
- `docs/SCOPE_PROGRESS.md` — 進捗更新

### 期待効果
- ADXによる相場状態判定でダマシシグナル大幅削減（トレンド中の逆張り、レンジ中のトレンドフォロー）
- 3段階利確で利益の取りこぼし防止（早期に一部確定しつつ大きなトレンドも追随）
- ポジション集中で1銘柄あたりの利益額が2倍に
- 確認待ち短縮でエントリータイミングが1日改善
- 出来高<0.7倍の低流動性銘柄を完全排除
- 昼休み時間帯のダマシ取引を完全排除

---

## Phase 24: 取引頻度改善 — リスク緩和・シグナル強度閾値修正（2026-03-05）

### 背景
- Phase 22でminSignalStrength=2に引き上げたが、強度2以上の買いシグナルが全件risk_blockedされ取引が成立しない状態
- 過去2週間でsuccessした買い12件は全て強度1（Phase 22以前の設定期間）
- ポートフォリオ集中上限30%と1取引損失率上限10%が厳しすぎ、強度2-3の良質シグナルもブロック
- Vercelフロントエンドで実行ログが表示されない問題（最新コード未デプロイ）

### 対応内容
1. **minSignalStrength引き下げ**: 2→1（強度1のシグナルでも取引可能に復帰）
2. **ポートフォリオ集中上限緩和**: maxPositionPercent 30%→40%
3. **1取引最大損失率緩和**: maxLossPerTrade 10%→15%（ATR損切り距離に適合）
4. **最大保有銘柄数復帰**: maxOpenPositions 5→10（1銘柄10万円で分散）
5. **DBマイグレーション**: Phase 24マイグレーション追加（旧値→新値の条件付きUPDATE）
6. **Vercel再デプロイ**: kabu-signal-naviに最新コードをデプロイ、実行ログ表示を復旧

### 変更ファイル
- `backend/src/services/auto_trade_service.py` — 修正1（DEFAULT_CONFIG.minSignalStrength）
- `backend/src/services/risk_service.py` — 修正2, 3, 4（DEFAULT_RISK_RULES）
- `backend/src/main.py` — 修正5（Phase 24 DBマイグレーション）

### 期待効果
- 強度1の買いシグナルが取引対象に復帰（過去実績で12件success実績あり）
- リスク制約の緩和で強度2-3の良質シグナルも通過可能に
- 10銘柄分散でポートフォリオ集中ブロックの解消
