# スコープ進捗管理

## 現在のステータス（2026-05-21 時点）

| 項目 | 状態 |
|------|------|
| 最終フェーズ | Phase 43（vmIdleTimeout=-1／ワークツリー未コミット） |
| 最終コミット | 56574b1（2026-05-15、Phase 39-40） |
| 進行中の調査 | **Code=100378 発注拒否の根本原因究明（5/15〜継続中、5/20も検証材料取れず）** |
| フロントエンド | Vercel稼働中（kabu-signal-navi.vercel.app） |
| バックエンド | Render稼働中（stock-signal-api-u9al.onrender.com） |
| ローカルバックエンド | **systemdサービス常時稼働（stock-backend.service）** |
| DB | Neon PostgreSQL稼働中 |
| 自動売買 | **実資金モード（dryRun=false）** |
| 証券口座残高 | 100,187円（2026-05-19 API確認） |
| 保有ポジション | ランド(8918) 1株（含み損 -53円） |
| 実資金確定損益 | ¥0（自動売買による約定実績なし） |
| 全ページ | 11ページ完了 |
| 全API | 45エンドポイント完了（+1: brokerage/health） |
| 運用ルール | **平日 11:20 までに kabu STATION 手動ログイン**（11:30初回スケジュール） |

### 実資金運用状況（2026-05-11）
- kabu STATION API接続確認済み（localhost:18080、トークン取得成功、5/11再確認）
- 証券口座残高: 100,187円（API経由で確認）
- 保有: ランド(8918) 1株（テスト購入分、含み損-52円）
- **5/1〜5/8の注文77件は全て失敗**（原因: 取引時間外発注 + パラメータバグ + 認証エラー）
- **5/11 自動ログイン設定のスキーマバグ修正（Phase 36）**:
  - BrokerageConfigUpdateRequest/ResponseにloginId/loginPassword未定義 → 追加
  - これまでloginId/loginPasswordがDB保存されず、セッション切れ時の自動再ログイン（Phase 34）が毎回「ログインID/パスワード未設定」で失敗していた
  - loginId/loginPassword をDB保存済み → 自動再ログインが機能する状態に
- 実際の自動売買約定: 0件、実資金損益: ¥0
- 次回取引: 5/12（月）09:30〜
- 現在の買いシグナル(強度≥2): 9銘柄（NTT, ソニー, JT, 東急不HD, トヨタ, 任天堂, 味の素, 三井物産, コナミ）

### ドライラン実績（Render上、3/13〜4/28、累計255取引）
- 確定損益: +¥15,343 / 含み損益: +¥20,054 / **トータル: +¥35,397（+5.04%）**
- 保有8銘柄: TDK(+13.3%), 信越化学(+8.6%), 味の素(+5.5%), LINEヤフー(+5.6%), 伊藤忠(+1.5%), ブリヂストン(+1.0%), 資生堂(-0.2%), NTT(-0.8%)
- ※4/20時点の+49,997円(+9.58%)から直近の相場変動で含み益縮小

### 実資金運用設定
| 項目 | 値 |
|------|-----|
| dryRun | false（実資金） |
| enabled | true |
| investmentBudget | 100,000円 |
| minSignalStrength | 1 |
| maxTradesPerDay | 15回/日 |
| maxOpenPositions | 1 |
| orderType | market（成行） |
| takeProfitPercent | 10% |
| stopLossPercent | -5% |

### 実資金移行ステータス — 全完了
- [x] 入金反映済み（1,000円、買付可能額1,000円）
- [x] ランド(8918) 1株 11円でプチ株買注文済み（2026-04-21）
- [x] 約定済み（2026-04-22、三菱より約定通知受領）
- [x] 投資経験を「株式現物取引: 1年未満」に更新（2026-04-26）
- [x] 信用取引口座の開設申込（2026-04-26）
- [x] 信用取引口座の開設完了確認（2026-04-27）
- [x] Professional昇格確認（2026-04-28確認済み）
- [x] kabuステーションAPI申込・有効化確認（2026-04-28）
- [x] 接続テスト — WSL→kabu STATION接続成功（2026-04-28）
  - localhostForwarding=true でWSL→localhost:18080転送が安定動作
  - DB設定をhost=localhost, apiPassword=本番用に更新
- [x] dryRun=false切替（2026-04-28）
- [x] 証券口座への入金（100,000円、三菱UFJ即時入金、2026-04-29）
- [x] 残高確認（100,187円、API経由で確認済み）
- [x] バックエンドsystemdサービス化（2026-05-01、Phase 30）
- [x] API認証リトライ機構追加（2026-05-02、Phase 31コミット済み）
- Windowsファイアウォールルール追加済み（WSL→18080/18081ポート許可）
- 起動時マイグレーションの上書きバグ修正済み（Phase 26 minSignalStrength/maxTradesPerDay, Phase 20 investmentBudget）

### 進行中の調査（5/19 時点）— Code=100378 発注拒否の根本原因
- **症状**: 5/15以降、auto-tradeの発注が全件 `Code=100378「指定された市場でのお取引はお受けできません」`で失敗。5/19も2件（4755, 9501）失敗、実現損益¥0
- **潰した仮説**: kabu STATION API設定 / ペイロード形式 / 銘柄固有問題 / 口座契約 / API契約未申込（すべて否定済）
- **今晩特定した有力原因**: **Exchange パラメータの市場ミスマッチ**
  - GUI 確認画面の「市場」欄が **「東証+」**（時間外PTS等の代替市場）と表示
  - kabu STATION は時間外、自動で東証+へルーティング
  - 一方コードは `Exchange: 1`（東証）固定 → 時間外は弾かれる
- **未解決の謎**: ザラ場時間中（5/19 14:12 / 14:32 / 15:02 JST）の発注も全て100378 → 「時間外」だけでは説明つかない
- **明朝の検証準備**: `scripts/diag-market-test.sh` を crontab で `2026-05-20 09:31 JST` 1ショット実行（8918/100株/指値5円・非約定）。ログ: `backend/logs/diag_market_test.log`
- **担当**: (1) kabu API Exchangeコード（PTS/東証+）の仕様調査、(2) ザラ場中失敗の仮説立て直し

#### 5/20 実況（検証材料は得られず）
- 09:31予定の `diag-market-test.sh` は **WSL VMが昨夜23:56〜本日14:42までダウン** していたため未実行（`backend/logs/diag_market_test.log` 0バイトのまま）
- 14:42 WSL復活 → 14:43 backend自動起動 → 14:44キャッチアップは kabu未ログインで401（全銘柄スキップ）
- 14:50頃 ユーザー手動ログイン → `/api/brokerage/connect` 成功
- 14:51 手動 `/api/auto-trade/run` 実行（50シグナル評価、約定0）
  - 強度2 buy: **9501 東電**（@544.3, qty=100）→ `risk_blocked`「損切りラインまで10.6%（上限10%）」※ ATR×2ベース、上限ギリギリ超過で拒否
  - 強度2 buy: 8830, 3659 → `予算不足で購入数量が0`
  - 強度2 sell: 8316, 9432, 8306 → `保有数量が0のため売却不可`
  - 結局 Code=100378 を踏む発注が1件も走らず、Exchange仮説の検証材料は明朝に持ち越し
- Phase 41 として登録していた発注拒否の真因特定は 5/21 朝（diag-market-test再実行）に再リトライ

### 直近の主要改善履歴
- Phase 43（5/21）: **WSL2 VM 永続化（vmIdleTimeout=-1）**。Phase 42 タスクは正しく 11:02:54 に発火していたが、`.wslconfig` の `vmIdleTimeout` 未指定（既定60秒）により wake action `/bin/true` 終了直後の60秒後に VM がアイドル落ち → 11:03 SIGTERM で systemd / uvicorn 道連れ → 21:38 手動復旧まで停止 → ザラ場 09:30-15:30 全枠スキップ → 実損益 ¥0。`/mnt/c/Users/taka5/.wslconfig` に `vmIdleTimeout=-1` 追記。一度起こせばPC再起動まで VM 維持される。保険として `KabuSignalAutoStart` に平日 09:00〜16:00 の 30分毎リピート（XML: `C:\Users\taka5\KabuSignalAutoStart.xml`）を用意したが、上書き登録には管理者権限が必要のため未適用。
- Phase 42（5/20）: **WSL自動起動タスク化**。`KabuSignalAutoStart`（Windowsタスクスケジューラ、トリガ: ログオン時 + 平日09:00、Action: `wsl.exe -d Ubuntu -- /bin/true`）を登録。Phase 37で作成済みだった `setup-windows-autostart.ps1` は未実行だったため `KabuSignalAutoStart` タスクは存在せず、5/20朝の WSL ダウン → 14:42 まで未復帰 → 11:30〜14:30 の全スケジュール枠スキップという事象を踏んで対処。残るギャップ: ザラ場中（09:00〜15:30）にWSL落ちした場合は次の09:00まで救えない（運用上は手動 `wsl.exe -d Ubuntu -- /bin/true` で対応） → Phase 43 で vmIdleTimeout=-1 にて根本対処
- Phase 40（5/15）: 接続ヘルス監視＋テスト基盤
- Phase 39（5/15）: 実残高ベース数量縮小（投資予算 vs 実残高の差異対応）
- Phase 38（5/13）: OSレベルスリープ抑止（kabu APIセッション断の実地観測ベース）+ Windowsスリープ起因の沈黙対策
- Phase 37（5/12）: kabu STATION認証復旧運用化。原因: systemd配下のuvicornのPATHに`powershell.exe`なし→自動再起動が失敗していた + auto-login.ps1がENTER後の座標クリックで口座番号欄にloginPasswordを連結入力するUI自動化バグ。修正: (1) `POWERSHELL_EXE`絶対パス化、(2) `kabu_auto_login.ps1`をTAB遷移+各Type前Ctrl+A+Delに変更、(3) `/api/brokerage/connect` 既定 `force_restart=false`（ライブセッション破壊防止）、(4) スケジューラを11:30開始に変更（前場前半捨てる代わり、11:20までに手動ログインで運用）
- Phase 35（5/8）: 注文パラメータ根本修正4件（Symbol/@1除去・FundType→AA・単元株丸め・取引時間ガード）+ 祝日カレンダー。検証API(18081)で買い/売り両方成功確認済み
- Phase 34（5/7）: kabu STATION自動再起動（認証エラー/接続エラー時にWSL→PowerShell経由で自動再起動→リトライ）+ 接続ヘルス監視（DB永続化・APIエンドポイント・フロントエンド警告バナー）
- Phase 33（5/5）: kabu STATION接続事前チェック（実資金モード時、銘柄処理前に接続確認）
- Phase 32（5/5）: 注文失敗伝播バグ修正（brokerage failed時にsuccess記録されるバグ）+ 架空データクリーンアップ
- Phase 31（5/1）: kabu STATION API自動リトライ（401時にトークン再取得×3回）
- Phase 30（5/1）: バックエンド常時稼働化（systemd Restart=always + enable-linger）
- Phase 29（5/2）: テスト実装（pytest 73件 + vitest 13件）+ Rate Limit（slowapi）
- Phase 26-28（3/9〜3/13）: 取引実行率・R/R比改善、損切りバイパスの重大バグ修正
- 現在のR/R比: 2:1（ATR利確4×ATR / ATR損切り2×ATR）
- 段階利確: 3段階（1.5×/2.5×/4.0×ATR）
- 損切りチェック: 全シグナルで発動（Phase 28バグ修正済み）

---

## フェーズ進捗

- [x] Phase 1: 要件定義
- [x] Phase 2: Git管理
- [x] Phase 3: フロントエンド基盤
- [x] Phase 4: バックエンド基盤
- [x] Phase 5: 機能実装
- [x] Phase 6: テスト・デプロイ（デプロイ済み、テスト実装済み）
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
- [x] Phase 25: 取引利益率の大幅改善（エントリー精度・イグジット最適化）
- [x] Phase 26: 取引実行率・利益率の根本改善
- [x] Phase 27: R/R比改善・イグジットロジック根本修正
- [x] Phase 28: 損切りバイパスバグ修正・ログ詳細化
- [x] Phase 29: テスト実装・Rate Limit
- [x] Phase 30: バックエンド常時稼働化・再発防止
- [x] Phase 31: kabu STATION API自動リトライ
- [x] Phase 32: 注文失敗伝播バグ修正・架空データクリーンアップ
- [x] Phase 33: kabu STATION接続事前チェック・認証失敗ログ強化
- [x] Phase 34: kabu STATION自動再起動・接続ヘルス監視
- [x] Phase 35: 注文パラメータ根本修正・取引時間ガード・祝日判定
- [x] Phase 36: 自動ログイン設定スキーマ修正（loginId/loginPassword保存可能化）
- [x] Phase 37: kabu STATION認証復旧運用化（PowerShellパス絶対化・auto-login.ps1 UIバグ修正・/connectをsafe-default化・スケジューラ11:30開始）
- [x] Phase 38: OSレベルスリープ抑止・Windowsスリープ起因の沈黙対策
- [x] Phase 39: 実残高ベース数量縮小（投資予算 vs 実残高の差異対応）
- [x] Phase 40: 接続ヘルス監視＋テスト基盤
- [ ] Phase 41（調査中）: Code=100378 発注拒否の根本対処（Exchange値の動的切替 / 時間外PTS発注対応 / ザラ場中失敗の真因特定）— 5/20は検証材料取れず（WSLダウン+リスク拒否で発注不発）
- [x] Phase 42: WSL自動起動タスク化（KabuSignalAutoStart: onLogon + 平日09:00）

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
| GET | `/api/brokerage/health` | 証券API接続ヘルス | [x] | [x] |
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
- [x] 証券会社連携サービス（kabu STATION API・注文・残高・ポジション・認証リトライ機構・自動再起動・接続ヘルス監視）
- [x] 自動売買サービス（シグナル連動・ドライラン・ATR動的損切り/利確・3段階利確・トレーリングストップ・時間帯重み・昼休み実行禁止・全ケースログ記録・実現/含み損益計算・重複買い防止・ドライラン仮想ポートフォリオ対応リスク評価）
- [x] 定期更新スケジューラ（09:30〜15:30の30分ごと + アラート・自動売買連動 + watchdog復帰対策）
- [x] CORS設定（Vercelサブドメイン正規表現対応）
- [x] グレースフルシャットダウン（SIGTERM対応）
- [x] Rate Limit（slowapi: 60リクエスト/分/IP）
- [x] 簡易マイグレーション（起動時ALTER TABLEによる列追加・エラーログ・検証付き）
- [ ] データベースマイグレーション（Alembic未導入、`create_all`+ALTER TABLEで代用）

### インフラ・デプロイ
- [x] フロントエンド: Vercel（`vercel.json` + `kabu-signal-navi.vercel.app`）
- [x] バックエンド（常時稼働）: Render（`render.yaml` + `stock-signal-api-u9al.onrender.com`）
- [x] バックエンド（ローカル）: cloudflaredトンネル経由（証券会社API連携用）
- [x] DB: Neon PostgreSQL（常時稼働）
- [x] PC起動時自動起動（systemd + WSL自動起動 + enable-linger）
- [x] 起動スクリプト（`start.sh` - バックエンド+トンネル一括起動・URL自動登録・バイナリログ対応）
- [x] ローカルバックエンド常時稼働（systemd `stock-backend.service` Restart=always）
- [x] WSLスリープ復帰対策（5分間隔watchdog + 起動時キャッチアップ）
- [ ] CI/CDパイプライン（未構築）

### テスト
- [x] バックエンドテスト（pytest: 73テスト — サービス層ユニットテスト + API統合テスト）
- [x] フロントエンドテスト（vitest: 13テスト — コンポーネントテスト）

---

## 未対応項目まとめ

| 項目 | 優先度 | 備考 |
|------|--------|------|
| ~~テスト実装（フロント/バック）~~ | ~~中~~ 済 | ~~テストフレームワーク未導入~~ Phase 29で実装済み（pytest 73件 + vitest 13件） |
| ~~Rate Limit~~ | ~~中~~ 済 | ~~要件定義では1分60リクエスト~~ Phase 29でslowapi導入済み |
| Alembicマイグレーション | 低 | 現状`create_all`+ALTER TABLEで動作中 |
| CI/CDパイプライン | 低 | 現状は手動デプロイ |
| カスタムフック分離 | 低 | 現状はページ内にインライン |
| Cloudflare Named Tunnel | 低 | 現状Quick Tunnel（URL変動）で運用中。ドメイン取得で固定URL化可能 |
| バックエンドプロセス監視 | ~~中~~ 済 | ~~start.shでuvicornが落ちても再起動されない~~ watchdog実装済み + systemd Restart=always（Phase 30） |
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

---

## Phase 25: 取引利益率の大幅改善（2026-03-06）

### 背景
- 12日間のドライラン実績: 確定損益+127円（ほぼ横ばい）、勝率25%（1勝3敗）
- 62件の買い注文がrisk_blocked、146件の売りシグナルがスキップ
- 根本原因: エントリー精度の低さ（minSignalStrength=1で弱シグナルでもエントリー）、ブレイクイーブンストップの早期退出、ポジション分散しすぎ

### 対応内容
1. **エントリー精度向上**: minSignalStrength 1→2（複数指標合致を必須化、弱シグナルでの無駄なエントリー排除）
2. **ポジション集中**: maxOpenPositions 10→5（1銘柄20万円で利益額確保、段階的利確も機能しやすく）
3. **ブレイクイーブンストップ緩和**: 発動条件 1×ATR→2×ATR（通常変動での早期退出防止）
4. **トレーリングストップ幅拡大**: 1×ATR→1.5×ATR（利益をより伸ばす）
5. **RSI 50ラインクロス新シグナル**: RSI_Above50(0.5,買)、RSI_Below50(0.5,売)。トレンド方向確認の補助シグナル
6. **ADX>40過熱警告**: OverheatedTrendタグ、全シグナル×0.7ペナルティ + カウンタートレンド×0.5追加ペナルティ（トレンド終了リスク回避）
7. **出来高データなし時ペナルティ**: NoVolDataタグ、スコア×0.5（確認なし取引の品質確保）
8. **11:00時間帯を実行禁止**: 0.9→0.0（昼休み前の低流動性時間帯を完全排除）

### 変更ファイル
- `backend/src/services/stock_service.py` — 修正5, 6, 7（RSI50クロス・ADX過熱・出来高NoVolData）
- `backend/src/services/auto_trade_service.py` — 修正1, 3, 4, 8（minSignalStrength・ブレイクイーブン・トレーリング・11:00禁止）
- `backend/src/services/risk_service.py` — 修正2（maxOpenPositions）
- `backend/src/main.py` — Phase 25 DBマイグレーション
- `frontend/src/components/BuyRecommendationCard.tsx` — 新シグナルラベル追加（RSI50超え・出来高不明・過熱トレンド）
- `frontend/src/components/SellRecommendationCard.tsx` — 新シグナルラベル追加（RSI50割れ・出来高不明・過熱トレンド）

### 期待効果
- minSignalStrength=2で弱シグナルエントリーを排除し勝率向上
- ブレイクイーブン2×ATR + トレーリング1.5×ATRで小さな調整での早期退出を防止
- 1銘柄20万円でポジション集中、利益額が倍増
- ADX過熱警告でトレンド終了間際の逆張り被弾を回避
- RSI 50ラインクロスで追加のトレンド方向確認

---

## Phase 26: 取引実行率・利益率の根本改善（2026-03-09）

### 背景
- ドライラン実績: 確定損益-4,283円、勝率20%（1勝4敗）、実行率1.9%（1,097件中21件）
- 逆説的現象: 強度3→成功率0%（全リスク拒否）、強度1→成功率31%（閾値で切られていた）
- risk_blocked 103件（maxOpenPositions 46件、maxLossPerTrade 44件）

### 対応内容
1. **minSignalStrength**: 2→1（強度1の31%成功率を活用）
2. **maxOpenPositions**: 5→8（1銘柄12.5万円、保有上限拒否46件を解消）
3. **maxLossPerTrade**: 15→20%（ATR損切り3×ATRに適合、拒否44件を解消）
4. **maxPortfolioLoss**: 10→15%（ポートフォリオ損失許容拡大）
5. **ATR損切り**: 2.5→3×ATR（通常変動での損切り多発を防止）
6. **段階利確閾値引き下げ**: 第1段階 2.5→2.0×ATR、第2段階 3.5→3.0×ATR
7. **段階利確最低株数**: 3→2株（少量保有でも利確可能に）
8. **トレーリング/ブレイクイーブン開始**: 2→1.5×ATR
9. **maxTradesPerDay**: DB古い値3→15に修正

---

## Phase 27: R/R比改善・イグジットロジック根本修正（2026-03-12）

### 背景
- マイナス収益が継続。根本原因の分析で以下が判明:
  - 利確が早すぎ（1.5×ATRでブレイクイーブン/トレーリング発動 → 少しの含み益ですぐ利益0で退出）
  - 損切りが遅すぎ（3×ATR → 負ける時は大きく負ける）
  - R/R比が1.67:1（5×ATR利確 : 3×ATR損切り）で、勝率37%以上が必要だが実績20%
  - ブレイクイーブンとトレーリングが同じ閾値（1.5×ATR）で実質バグ
  - 段階利確がhold_qty>=2制限で小ポジション（1-2株）では利確不能

### 対応内容
1. **R/R比 2:1 に改善**: ATR損切り 3→2×ATR、ATR利確 5→4×ATR（stock_service + auto_trade_service両方）
2. **段階利確閾値引き下げ**: 第1段階 2.0→1.5×ATR、第2段階 3.0→2.5×ATR、第3段階 5.0→4.0×ATR
3. **段階利確最低株数撤廃**: hold_qty>=2制限 → max(hold_qty//3, 1)で1株保有でも利確可能
4. **トレーリング閾値引き上げ**: 1.5→2.5×ATR開始、トレーリング幅 1.5→2.0×ATR（早期退出防止）
5. **ブレイクイーブン閾値引き上げ**: 1.5→3.0×ATR開始（十分利益が伸びてから発動）
6. **評価順序変更**: 段階利確→ブレイクイーブン→トレーリング→損切り（旧: トレーリング→ブレイクイーブン）
7. **リスクルール適正化**:
   - maxLossPerTrade: 20→10%（ATR 2×ATR損切り=約4-6%に整合）
   - maxPositionPercent: 40→50%（空ポートフォリオ初回取引拒否を緩和）
   - maxPortfolioLoss: 15→20%（早期全停止を防止）
8. **空ポートフォリオ対応**: total_value==0時はポジション比率チェックをスキップ

### 変更ファイル
- `backend/src/services/auto_trade_service.py` — 修正1-6（ATR倍率・段階利確・トレーリング・ブレイクイーブン・評価順序）
- `backend/src/services/risk_service.py` — 修正7, 8（リスクルール・空ポートフォリオ対応）
- `backend/src/services/stock_service.py` — 修正1（ATR利確/損切り倍率）
- `backend/src/main.py` — Phase 27 DBマイグレーション
- `frontend/src/pages/RiskSettings.tsx` — デフォルト値更新

### 期待効果
- R/R比 2:1 で勝率33%でも損益分岐（旧: 37%必要）
- ATR損切り 2×ATR で損失幅が33%縮小（3×ATR比）
- 早期段階利確（1.5×ATR〜）で小さな利益も確実に確保
- トレーリング/ブレイクイーブンの閾値分離で「含み益→利益0退出」パターンを解消
- 1株保有でも段階利確が機能し、少額投資の利益効率改善

---

## Phase 28: 損切りバイパスバグ修正・ログ詳細化（2026-03-13）

### 問題分析
- 確定損益+283円、含み損益-8,670円、トータル-8,387円(-1.1%)
- 8銘柄保有中、5銘柄が含み損（-3.3%〜-4.1%）だが損切りが一度も発動しない
- ATR損切り=2×ATR（約4-6%）設定なのに-4%超のポジションが放置されている

### 根本原因（重大バグ）
- **イグジットロジック（損切り/利確/トレーリング）が `hold` シグナル時しか実行されなかった**
- 株価が下落 → RSI低下 → `buy`シグナル発生 → 「既に保有中」でスキップ → **損切りチェックが完全バイパス**
- 例: トヨタ 3,495円購入→3,377円下落(-3.4%)→RSI低下で`buy`シグナル→損切り未実行
- Phase 16（2026-02-24）以来、約3週間この状態だった

### 修正内容
1. **イグジットチェックをシグナル種別非依存に変更** — `if signal == 'hold':` → `if hold_qty > 0:` で全シグナルで保有チェック
2. **フロー整理**:
   - hold + 保有中: イグジットチェック → 発動なら売り → なければ「様子見」ログ + skip
   - buy + 保有中: イグジットチェック → 発動なら売り → なければ「保有中」ログ + skip
   - sell + 保有中: イグジットチェック → 発動なら売り → なければ通常sell処理へ
   - hold + 未保有: 「様子見」ログ + skip
   - buy/sell + 未保有: 通常buy/sell処理へ
3. **ログ詳細化**: 個別銘柄ごとに EXIT/HOLD/RISK_BLOCKED/EXECUTE ログを出力（entry/current/gain%/ATR/SL/TP情報つき）

### 変更ファイル
- `backend/src/services/auto_trade_service.py` — イグジットチェックのガード条件修正、詳細ログ追加

### 期待効果
- ATR損切り（2×ATR）が全シグナルで正しく発動し、含み損放置を防止
- 段階利確・トレーリング・ブレイクイーブンも同様にbuy/sellシグナル中でも発動
- ログにentry/current/gain%/ATR値が出力され、翌日以降の判断根拠が追跡可能

---

## Phase 29: テスト実装・Rate Limit（2026-04-23）

### 対応内容

#### バックエンドテスト（pytest: 73テスト）
1. **テスト基盤**: pytest + pytest-asyncio、SQLiteインメモリDB（StaticPool）、lifespan除外テスト用FastAPIアプリ
2. **StockServiceテスト（20件）**: テクニカル指標計算（RSI/MACD/SMA/BB/ATR/Stoch/WillR/ADX）、シグナル判定ロジック、設定CRUD、銘柄CRUD
3. **RiskServiceテスト（10件）**: リスクルールCRUD、取引リスク評価（初回取引/最大保有数/損失率）、チェックリスト、価格提案
4. **AutoTradeServiceテスト（15件）**: 設定CRUD、銘柄別設定、ログ取得、保有数量計算、平均取得単価、時間帯重み
5. **API統合テスト（27件）**: stocks/settings/transactions/risk/auto-trade/alertsの主要エンドポイント

#### フロントエンドテスト（vitest: 13テスト）
1. **テスト基盤**: vitest + @testing-library/react + jsdom
2. **SignalStrengthDisplay（5件）**: 強度1-3のラベル表示、強度0の非表示、showLabel制御
3. **BuyRecommendationCard（5件）**: 銘柄情報表示、シグナルラベル、購入提案の表示/非表示
4. **BudgetSetting（3件）**: 予算表示、ダイアログ開閉、プリセット金額表示

#### Rate Limit
- **slowapi 0.1.9** 導入: 全エンドポイントに `60リクエスト/分/IP` のデフォルト制限
- `main.py` に Limiter ミドルウェア + RateLimitExceeded ハンドラ追加

### 変更ファイル
- `backend/requirements.txt` — slowapi追加
- `backend/requirements-test.txt` — テスト用依存関係（新規）
- `backend/pytest.ini` — pytest設定（新規）
- `backend/tests/conftest.py` — テスト共通フィクスチャ（新規）
- `backend/tests/test_health.py` — 基盤動作確認テスト（新規）
- `backend/tests/test_stock_service.py` — StockServiceテスト（新規）
- `backend/tests/test_risk_service.py` — RiskServiceテスト（新規）
- `backend/tests/test_auto_trade_service.py` — AutoTradeServiceテスト（新規）
- `backend/tests/test_api.py` — API統合テスト（新規）
- `backend/src/main.py` — Rate Limit追加
- `frontend/package.json` — vitest/testing-library追加、testスクリプト追加
- `frontend/vite.config.ts` — vitest設定追加
- `frontend/src/test/setup.ts` — テストセットアップ（新規）
- `frontend/src/components/__tests__/SignalStrengthDisplay.test.tsx` — 新規
- `frontend/src/components/__tests__/BuyRecommendationCard.test.tsx` — 新規
- `frontend/src/components/__tests__/BudgetSetting.test.tsx` — 新規

---

## Phase 30: バックエンド常時稼働化・再発防止（2026-05-01）

### 背景
- 4/28にdryRun=falseに切り替え、4/30から実資金自動売買を開始する予定だった
- しかしバックエンドが4/28 13:43以降停止しており、実取引が一度も実行されなかった
- 原因: nohupによる手動起動でプロセス終了後の自動復旧がなかった

### 対応内容
1. **systemdユーザーサービス化**: `~/.config/systemd/user/stock-backend.service` を作成
   - `Restart=always` + `RestartSec=10` でクラッシュ時10秒後に自動再起動
   - `StartLimitBurst=5` / `StartLimitIntervalSec=300` で連続クラッシュ時の無限再起動を防止
2. **enable-linger**: `loginctl enable-linger taka5` でWSL再起動後もユーザーサービスが自動起動
3. **サービス有効化**: `systemctl --user enable stock-backend.service` で永続有効化

### 変更ファイル
- `~/.config/systemd/user/stock-backend.service` — 新規

### 管理コマンド
```
systemctl --user status stock-backend    # 状態確認
systemctl --user restart stock-backend   # 再起動
systemctl --user stop stock-backend      # 停止
journalctl --user -u stock-backend -f    # ログ監視
```

---

## Phase 31: kabu STATION API自動リトライ（2026-05-01）

### 背景
- kabu STATIONの再起動後にAPIトークンが失効し、手動でのトラブルシューティングが必要だった
- 実資金モードで注文失敗時にリトライせず、取引機会を逃すリスクがあった

### 対応内容
1. **`_request_with_retry`メソッド追加**: 全APIリクエストで401応答時にトークン再取得→リトライ（最大3回）
2. **`_ensure_token`メソッド追加**: トークン未取得時に自動で`connect()`を呼び出し
3. **各APIメソッドのリファクタ**: `get_balance`/`get_positions`/`send_order`/`cancel_order`を`_request_with_retry`経由に統一

### 変更ファイル
- `backend/src/services/brokerage_service.py` — KabuStationClientに自動リトライ機構追加

### 期待効果
- kabu STATION再起動後も自動で再認証され、手動対応が不要に
- 注文時の一時的な認証エラーでも取引機会を逃さない

---

## Phase 32: 注文失敗伝播バグ修正・架空データクリーンアップ（2026-05-05）

### 背景
- 実資金収支を確認したところ、brokerage_ordersの全7件がstatus=failedにもかかわらず、auto_trade_logにはsuccess、Transactionテーブルにも架空取引が記録されていた
- 原因: `BrokerageService.create_order`が注文失敗時に例外を握りつぶし（`except: print`）、呼び出し元に失敗が伝播しなかった
- 5/1の2件（トヨタ166株・キーエンス6株）と5/4の5件は全て約定していない架空データ

### 対応内容

#### DBクリーンアップ
1. **Transactionテーブル**: 架空の5件（7974/8053/9501/9766/7203）を削除
2. **auto_trade_log**: 誤successの7件をfailedに修正（executed=false, メモ追記）

#### コード修正
3. **`brokerage_service.py`**: `create_order`のexceptブロックで`print`→`logger.error` + `raise`に変更。例外を呼び出し元に伝播
4. **`auto_trade_service.py`（買い注文）**: `create_order`戻り値のstatusがfailedの場合`RuntimeError`を送出し、Transaction/ログの誤記録を防止
5. **`auto_trade_service.py`（売り注文）**: 同様のstatusチェックを追加

### 変更ファイル
- `backend/src/services/brokerage_service.py` — 例外再送出
- `backend/src/services/auto_trade_service.py` — 注文ステータスチェック追加（買い・売り両方）

### 修正の防御層
- **第1層**: `brokerage_service.create_order`が例外をraiseし、auto_trade_serviceのexceptブロックでfailedログ記録
- **第2層**: 万が一例外が出ずにfailedステータスで返却された場合もRuntimeErrorで検知

---

## Phase 33: kabu STATION接続事前チェック・認証失敗ログ強化（2026-05-05）

### 背景
- Phase 32で注文失敗の伝播バグは修正したが、kabu STATIONが接続できない状態で全銘柄の処理が走り、個別にfailedログが大量に溜まる非効率が残っていた
- 5/5にkabu STATION再起動で401が解消したが、認証失敗の原因がログから判別できなかった
- kabu STATIONはセッションが内部的に壊れると再起動が必要になることが判明

### 対応内容
1. **初回認証失敗の詳細ログ**: `KabuStationClient.connect`で401時にエラーコード・メッセージ・対処法をlogger.errorで出力
2. **実資金モード接続事前チェック**: `auto_trade_service`の銘柄処理ループ前に`brokerage_service.connect()`で接続確認。失敗時はSYSTEMログにfailed記録して即return（全銘柄スキップ）

### 変更ファイル
- `backend/src/services/brokerage_service.py` — 初回認証失敗時の詳細ログ + トークン取得成功ログ
- `backend/src/services/auto_trade_service.py` — 実資金モード接続事前チェック追加

### 期待効果
- kabu STATION接続不可時に即座に検知し、無駄な個別注文失敗ログの大量発生を防止
- ログに「kabu STATIONの再起動が必要な可能性があります」と具体的な対処法が記録される
- ドライランモードには影響なし（事前チェックをスキップ）

---

## Phase 34: kabu STATION自動再起動・接続ヘルス監視（2026-05-07）

### 背景
- 5/6〜5/7にかけてkabu STATIONの認証エラー（4001007）が継続し、自動売買が完全停止
- Phase 31のトークンリトライ機構はトークン期限切れの対策であり、kabu STATION自体のAPI認証固着には無力
- 接続失敗がログに埋もれ、ユーザーが気づくまで数日間放置される問題
- kabu STATIONはセッションが固着すると再起動以外に復旧方法がないことが確認済み

### 対応内容

#### kabu STATION自動再起動
1. **`_restart_kabu_station`メソッド**: WSLからPowerShell経由でkabu STATIONを`Stop-Process → Start-Process`で自動再起動
2. **プロセス起動確認**: 最大30秒間、5秒ごとに`Get-Process KabuS`でPID確認
3. **`_connect_with_restart`メソッド**: 再起動後に最大3回リトライで再接続
4. **`connect`メソッド改修**: 接続エラー（ConnectError）・認証エラー（401）・その他例外すべてで自動再起動→リトライを発動

#### 接続ヘルス監視
5. **`BrokerageHealth`モデル**: status/consecutive_failures/last_success_at/last_failure_at/last_error_messageをDB永続化
6. **`_record_success`/`_record_failure`**: 接続結果をDB記録。3回連続失敗でCRITICALログ出力
7. **`GET /api/brokerage/health`エンドポイント**: 接続ヘルス状態をJSON返却
8. **`GET /api/health`拡張**: ヘルスチェックに証券API接続状態を含める

#### 注文パラメータ修正（FundType欠落バグ）※Phase 35で再修正
5a. **`send_order`に`FundType`パラメータ追加**: 現物買い='02'（保護預り）、現物売り='  '（半角スペース2つ）→ **Phase 35で'AA'に再修正**
5b. **`DelivType`を売買方向で分岐**: 買い=2（お預り金）、売り=0（指定なし）
5c. **注文エラー詳細ログ**: 400/500エラー時にレスポンスボディをログ出力

#### フロントエンド警告バナー
9. **StockList（銘柄一覧）ページ**: 接続エラー時に赤バナー「証券API接続エラー（N回連続失敗）- 自動売買が停止しています」
10. **AutoTradeSettings（自動売買設定）ページ**: 詳細な接続エラーバナー（エラーメッセージ・最終成功/失敗時刻表示）
11. **60秒ごと自動リフレッシュ**: brokerageHealthクエリを60秒間隔でポーリング

### 動作確認結果
| テストシナリオ | 結果 | 所要時間 |
|---------------|------|---------|
| kabu STATION停止 → 自動起動 → 接続 | 成功 | ~33秒 |
| 認証エラー(401) → 自動再起動 → 接続 | 成功 | ~33秒 |
| FundType付き注文 → パラメータ変換エラー解消 | 成功 | — |
| 取引時間外の注文 → 「銘柄が見つからない」（正常） | 確認済み | — |

### 変更ファイル
- `backend/src/models/stock.py` — BrokerageHealthモデル追加
- `backend/src/services/brokerage_service.py` — 自動再起動・ヘルス追跡・connect改修
- `backend/src/routers/brokerage.py` — `/api/brokerage/health`エンドポイント追加
- `backend/src/main.py` — `/api/health`に証券API状態を含める
- `frontend/src/types/index.ts` — BrokerageHealth型追加
- `frontend/src/api/client.ts` — getBrokerageHealth API追加
- `frontend/src/pages/StockList.tsx` — 接続エラー警告バナー追加
- `frontend/src/pages/AutoTradeSettings.tsx` — 接続エラー詳細バナー追加

### 防御の層（Phase 31〜34）
- **第1層（Phase 31）**: APIトークン期限切れ → トークン再取得リトライ（3回）
- **第2層（Phase 33）**: 実資金モード実行前のkabu STATION接続事前チェック
- **第3層（Phase 34）**: 接続/認証エラー → kabu STATION自動再起動 → リトライ（3回）
- **第4層（Phase 34）**: ヘルス監視 → フロントエンド赤バナー表示 → ユーザーへの即時通知

---

## Phase 35: 注文パラメータ根本修正・取引時間ガード・祝日判定（2026-05-08）

### 背景
- 5/1〜5/7の実資金注文67件が全て400 Bad Requestで失敗
- Phase 34でFundType追加したが、値が間違っていた（'02'ではなく'AA'が正しい）
- Symbol形式もsendorderでは`@1`不要だった
- 取引時間外（21:42 JST等）にキャッチアップ実行で発注していた
- 数量が1株単位で送信され、単元株（100株）の倍数でなかった

### 根本原因分析
- 67件の注文失敗は**4つのバグの複合**。どれか1つでも残っていれば注文は通らない
- Phase 34では4つ中1つ（FundType追加）しか修正できておらず、その値も誤りだった

### 対応内容

#### 注文パラメータ修正（バグ1,2）
1. **Symbol形式修正**: `f'{code}@1'` → `code`（sendorderでは`@1`サフィックス不要）
2. **FundType修正**: 買い`'02'`→`'AA'`（auカブコム口座は預り金自動振替）

#### 数量計算修正（バグ3）
3. **単元株丸め**: `int(budget / price)` → `(int(budget / price) // 100) * 100`（100株単位に切り捨て）

#### 取引時間ガード（バグ4）
4. **実資金モード取引時間チェック**: 9:00-15:30以外は発注スキップ（ログ記録付き）
5. **昼休みガード**: 11:30-12:25は発注スキップ
6. **キャッチアップ時間制限**: `_should_have_run_today()`に取引時間内チェック追加

#### 祝日判定
7. **`_jp_holidays()`**: 日本の祝日カレンダー（15祝日 + GW振替休日）
8. **`_is_trading_day()`**: 平日チェックに祝日判定を追加

#### ログ強化
9. **sendorder詳細ログ**: 注文送信時にcode/side/qty/price、成功時にOrderId、失敗時にCode/Messageを出力

### 検証結果（検証用API 18081で実施）
| テスト | パラメータ | 結果 |
|--------|-----------|------|
| 買い注文 | Symbol='9501', FundType='AA', Qty=100 | **成功** |
| 売り注文 | Symbol='8918', FundType='  ', Qty=100 | **成功** |
| 祝日判定 | 5/4(月)みどりの日 | 休場判定 **正常** |
| 取引時間外 | 21:42 JST | 時間外判定 **正常** |

### 変更ファイル
- `backend/src/services/brokerage_service.py` — Symbol・FundType修正、sendorderログ強化
- `backend/src/services/auto_trade_service.py` — 取引時間ガード、昼休みガード、単元株丸め
- `backend/src/main.py` — 祝日カレンダー、取引時間チェック、キャッチアップ制限

### 修正した4つのバグと検証状況
| # | バグ | 修正前 | 修正後 | 検証 |
|---|------|--------|--------|------|
| 1 | Symbol形式 | `'9501@1'`（銘柄不明エラー） | `'9501'` | 検証API成功 |
| 2 | FundType | `'02'`（預り区分エラー） | `'AA'` | 検証API成功 |
| 3 | 数量 | 1株単位（単位株数エラー） | 100株単位切り捨て | 検証API成功 |
| 4 | 取引時間 | 時間外発注（市場エラー） | 9:00-15:30ガード | ロジックテスト済 |

---

## Phase 36: 自動ログイン設定スキーマ修正（2026-05-11）

### 背景
- Phase 34でkabu STATION自動再起動＋自動ログイン機能を実装したが、実際には一度も自動ログインが成功していなかった
- 原因: `BrokerageConfigUpdateRequest`/`BrokerageConfigResponse`スキーマにloginId/loginPasswordフィールドが未定義
- APIでloginId/loginPasswordをPUTしても、Pydanticバリデーションで無視されDB保存されなかった
- そのため`_restart_kabu_station()`が毎回「ログインID/パスワード未設定」で即失敗していた

### 対応内容
1. **`BrokerageConfigResponse`にフィールド追加**: loginId(str), loginPassword(str)
2. **`BrokerageConfigUpdateRequest`にフィールド追加**: loginId(Optional[str]), loginPassword(Optional[str])
3. **DB保存確認**: PUT /api/brokerage/config でloginId/loginPasswordが正常に保存・取得されることを確認

### 変更ファイル
- `backend/src/models/schemas.py` — BrokerageConfigResponse/BrokerageConfigUpdateRequestにloginId/loginPassword追加

### 影響
- Phase 34の自動再起動→自動ログインフローが初めて機能する状態になった
- セッション切れ時: 認証エラー検知 → kabu STATION再起動 → PowerShellスクリプトでログイン → API再接続
- Node.js 18→22アップグレード（nvm導入）もこのセッションで実施

---

## Phase 37: Windowsスリープ起因の沈黙対策（2026-05-13）

### 背景
- 5/13 12:35〜22:10の約9時間半、バックエンドが完全停止
- backend.log / server.log ともに**トレースバックなし**、uvicornのアクセスログまで途絶
- → Pythonクラッシュではなく**ホストOS（Windows）の S3 スタンバイ**が原因と判定
- `powercfg /a` 確認: スタンバイ(S3) / 休止状態 / 高速スタートアップ すべて有効
- 12:30スロットは正常動作（7974 HOLD、買いシグナル10銘柄はRISK_BLOCKED）。13:00以降の5スロットを全ミス

### 対応内容
1. **`StockAutoTrade-KeepAwake` タスク登録**
   - 平日 09:00 起動、`SetThreadExecutionState(ES_CONTINUOUS|ES_SYSTEM_REQUIRED)` で 16:00 までスリープブロック
   - 画面OFFは許可（`ES_DISPLAY_REQUIRED` は立てない）
   - `StartWhenAvailable` + `AllowStartIfOnBatteries` でノートPC対応
2. **`WSL Auto Start` タスク登録**
   - onlogon トリガで `wsl.exe -d Ubuntu -- systemctl --user start stock-backend.service` 起動
   - PC再起動後のバックエンド自動復旧を担保
3. **自己完結セットアップスクリプト**: `%TEMP%\stock-setup-all.ps1` 経由で UAC 昇格して両タスクを登録

### ハマりポイント
- `\\wsl.localhost\Ubuntu\...` UNC パスは **Windows の昇格セッションから不可視**（昇格は別ユーザーコンテキストで動作）
- 当初 `setup-all.ps1` を UNC 経由で実行 → "The system cannot find the file specified" で全タスク未登録のまま終了
- 回避策: `/mnt/c/Users/<user>/AppData/Local/Temp/` に自己完結スクリプトを書き、ローカルパスで昇格起動

### 変更ファイル
- `setup-keep-awake.bat`（新規・未コミット） — `register-keep-awake.ps1` 起動ラッパ
- `setup-wsl-autostart.bat`（新規・未コミット） — `WSL Auto Start` 登録
- `backend/scripts/setup-all.ps1`（新規・未コミット） — 統合セットアップ（UNC版・参考用）
- `backend/scripts/keep-awake.ps1` / `register-keep-awake.ps1`（既存）

### 検証結果（2026-05-13 22:30頃）
| タスク | 登録 | 次回実行 |
|--------|------|----------|
| StockAutoTrade-KeepAwake | OK | 2026-05-14 09:00 |
| WSL Auto Start | OK | onlogon |

### 防御の層（更新版）
- **第1〜4層（Phase 31〜34）**: API/接続レベルのリトライ・再起動・監視
- **第5層（Phase 37）**: ホストOSレベルの可用性 — スリープ抑止 + ログオン時自動起動

### 残課題
- 明日（5/14）11:30スロットからの試運用でスリープ抑止が効くか実地確認
- `_should_have_run_today()` キャッチアップが想定通り発火するか確認

---

## Phase 38: スリープ抑止のOSレベル強化＋kabu APIセッション断の実地観測（2026-05-14）

### 背景（Phase 37 試運用の結果）
- 5/14 12:40〜14:52 の約2時間、再びスケジューラが完全停止
- 12:30 スロットは正常完了（Trades today: 0、kabu接続OK）
- 13:00 / 13:30 スロットは **missed**、14:00 / 14:30 は 14:52 に遅延起動
- 復帰後 14:54 にkabu API token 取得で **HTTP 401 / Code=4001007**

### 原因分析
1. **Phase 37 KeepAwake タスクが今日一度も発火していなかった**
   - `Get-ScheduledTaskInfo`: `LastRunTime = 1999/11/30`（未実行）, `LastTaskResult = 267011`（SCHED_S_TASK_HAS_NOT_RUN）
   - `NextRunTime = 2026-05-15 09:00`
   - 5/13 22:33 にタスク登録 → 当日9:00を既に過ぎていたため初回トリガをスキップ、5/14 09:00 にも発火しないまま 5/15 にロールオーバーした疑い
   - スリープ抑止が無効 → ホストOSが12:40頃にスタンバイ突入 → 14:52に何らかの要因（マウス入力？）で復帰
2. **kabu STATION 内部APIセッションの消失**
   - スリープ復帰後、`POST /kabusapi/token` が `Code=4001007 ログイン認証エラー`
   - kabu STATION 画面上のAPIインジケータは緑（API利用ON）でログイン状態維持の見た目
   - DB側のAPIパスワード（`taketake36nhk`、13文字）は変更なし、12:30 の成功時と同一値
   - 「ツール → 設定 → API」でAPIパスワード再入力 → **保存しただけでは401継続**
   - **kabu STATION 本体を終了→再起動→再ログインで認証復活**（15:04:44）
   - → スリープ起因でkabuクライアント側の認証状態だけが内部的に劣化、GUIインジケータには反映されない挙動を確認

### 対応内容（今日入れた）
1. **OSレベルの電源設定で直接スリープ封殺**（タスクスケジューラに依存しない）
   ```powershell
   powercfg /change standby-timeout-ac 0
   powercfg /change hibernate-timeout-ac 0
   powercfg /h off
   ```
   - AC 接続中: スタンバイ無効 / 休止無効 / 休止機能そのものをOFF
   - `powercfg /a` で「休止状態は無効になっています」確認
   - Phase 37 タスクが万一未発火でもOSレベルで寝なくなる二重防御
2. **手動で kabu STATION 再起動 → /api/brokerage/connect (force_restart=false) で接続復活**を確認

### 取り逃した取引
- **15:00 スロット**: 接続復旧（15:04）前のため全銘柄スキップ
- 12:30以降、15:30まで実取引機会なし

### 「完全自動売買」の現実的な限界（議論結果）
- kabu STATION 依存である限り、以下は構造的に解決不可能
  - ホストOSスリープ起因のセッション断
  - APIインジケータ緑でも内部認証が落ちる挙動
  - 復旧に kabu STATION 本体再起動（GUI 操作）が必要なケース
- 国内ネット証券で完全REST／無人運用可能なAPIは実質なし
  - 楽天 MARKETSPEED RSS / 岡三RSS も同様にローカルアプリ常時起動が前提
- 純REST API での無人化は Interactive Brokers が現実的な唯一解だが、口座移管・手数料体系の違い・小口取引でのコスト不利から現状維持を選択
- 結論: **「壊れない自動売買」は諦め、「事故率を下げる＋早期検知」方針で運用継続**

### 防御の層（再更新）
- **第1〜4層（Phase 31〜34）**: API/接続レベルのリトライ・再起動・監視
- **第5層（Phase 37）**: タスクスケジューラ経由のスリープ抑止 + ログオン時WSL起動
- **第6層（Phase 38）**: `powercfg` によるOSレベル電源設定（タスク非依存の最終防衛線）

### 残課題
- Phase 37 KeepAwakeタスクが 5/15 09:00 に実際に発火するか確認
- 発火しなかった場合、トリガ設定（StartBoundary を当日にする / `StartWhenAvailable` の挙動）を見直し
- kabu API 401 検知時の自動 kabu STATION 再起動フローを「連続失敗N回 + 取引時間内」に限定して再有効化検討（Phase 34 の force_restart 経路）
- 401 発生時のスマホ/メール即時通知（取引機会逸失を最短で把握する仕組み）

---

## Phase 39: 実残高ベース数量調整＋当日重複発注防止（2026-05-15）

### 背景（5/15 当日稼働の結果）
- 手動ログイン・kabu API接続（終日 connected、最終成功 14:31:46）・スケジューラ・シグナル判定はすべて正常稼働
- ログ101件生成（skipped 94件 / failed 7件、buy 40 / sell 15 / hold 46）
- それでも **約定 0 件**。7件の買い注文（4911・4755・3659・9432、14:12 と 14:32 の2スロットで重複）はすべて kabu sendorder で **HTTP 500 Internal Server Error**

### 真因分析
1. **設定値と実残高の乖離**
   - `investmentBudget` = **1,000,000円**（DB設定）
   - 実残高 = **100,187円**（kabu API）
   - `maxOpenPositions` = **1**
   - 数量計算（`auto_trade_service.py:794-797`）が設定値だけを見るため、9432 NTT @151円 → **6,600株 ≒ 約100万円分** で発注 → 残高10万円では当然弾かれ kabu が 500 を返す
2. **発注前の残高検証が皆無**
   - `risk_service` は `maxPositionPercent`・`maxLossPerTrade`・`maxPortfolioLoss` といった**割合系**のみ
   - 「現金残高で買えるか」の**絶対額チェックが無く**、明らかな資金不足注文がそのまま kabu まで届いていた
3. **当日 failed 注文の再評価で重複発注**
   - 既存の `existing_qty` 判定は約定済み Transaction しか見ない
   - 同一スロット内（14:12 → 14:32）で同じ銘柄に再発注して 500 を量産

### 対応内容（5/15 夜に実装）
`backend/src/services/auto_trade_service.py` を修正：

1. **実残高取得**（実資金モード時のみ、kabu 接続OK確認直後に `brokerage_service.get_balance()` を呼ぶ）
2. **予算クランプ**: `effective_budget = min(settings['investmentBudget'], cash_balance)`
3. **数量縮小**: 注文額が `cash_balance × 0.95`（5%バッファ）を超える場合は単元株単位で自動縮小、それでも残高不足なら明示的にスキップログ
4. **当日重複発注防止**: 新ヘルパー `_has_today_buy_order(code)` で `BrokerageOrder` テーブルを参照し、同日 buy 注文（status不問・failed含む）が1件でもあれば次スロット以降スキップ

### 検証
- 構文OK（`python -c "import ast; ast.parse(...)"`）
- バックエンド再起動完了（旧 PID 307 停止 → 新規起動、`/api/health` で `healthy` 応答確認）
- 実地検証は **2026-05-18（月）11:30 スロット** が初回（取引時間外スキップが効くため夜間は試運転不可）

### 結論
- 「手動ログインさえすれば実資金売買が回る」想定は今日時点では **不成立**（手動ログインしてもコード側バグで全失敗）
- Phase 39 修正＋手動ログインが揃って初めて機能する状態
- 月曜以降の挙動で約定が発生するか、または別のkabu API 500 要因（パラメータ不一致など）が残っているかを実地で切り分ける

### 残課題
- 月曜 11:30 スロットで「実残高ベース数量縮小」が想定通り発火するか確認
- kabu sendorder のエラーレスポンス本文をログに残す改修（500の本当の理由を将来切り分けるため）
- 残高が極端に少ない（数千円規模）銘柄での「単元株が買えない」ケースの取り扱い検討（現状は「予算不足で購入数量が0」スキップ）

### 変更ファイル
- `backend/src/services/auto_trade_service.py` — 数量計算ロジック改修＋当日重複発注ガード追加（未コミット）

---

## Phase 40: Phase 39 実地検証＋約定ゼロの構造分析（2026-05-18）

### 背景
Phase 39（実残高ベース数量縮小＋当日重複発注防止）の初回実地検証日。手動ログインは 14:30 に完了。

### 当日稼働サマリ
- バックエンド起動 14:56、起動時 catch-up 実行（14:58-14:59）
- 定刻ジョブ: 15:00 と 15:30（15:31）の2スロット稼働
- kabu API 接続: 終日 connected（最終成功 15:01:43、`consecutiveFailures=0`）
- 実残高: **100,187円**（2回とも一致）
- 約定: **0件**
- 判定ログ: **101件** すべて skipped、kabu sendorder への発注ゼロ → **500 エラー再発なし**

### スキップ理由内訳
| 理由 | 件数 |
|---|---:|
| シグナル強度不足 (1 < 2) | 46 |
| holdシグナル（様子見） | 36 |
| 保有数量0で売却不可（空売り未対応） | 14 |
| シグナルデータなし | 2 |
| **予算不足で購入数量0** | **2** |
| 取引時間外 (15:31) | 1 |

### 強度2以上の有効シグナル（16件）
- **sell 14件**: いずれも未保有のため空売り不可で全スキップ（9501・8411・7267・6098・8306・4755・3289 ほか、強度3が複数）
- **buy 2件**: 8830（住友不動産）強度2 → 2サイクル連続「予算不足で購入数量0」スキップ

### 評価
1. **Phase 39 の修正は意図通り動作**
   - 「予算不足で購入数量が0」の明示的スキップが 8830 で2回発火
   - kabu sendorder への 500 エラー誘発リクエストが消滅（5/15 は7件の500、5/18 は0件）
   - 「実残高 100,187円 vs 設定 1,000,000円」乖離が安全側にクランプされている
2. **約定ゼロは Phase 39 のバグではなく構造要因**
   - 残高10万円ではbuy強度2候補（住友不動産など高単価株）に手が出ない
   - 売りシグナル多発は地合いが下げ基調で買い候補が乏しい
3. **保有 8918 ランド** 1株（含み損 -53円, 現値10円）はsell強度2以上の発火なしで保持継続

### スリープ抑止の効果
- Phase 37（タスクスケジューラ KeepAwake）と Phase 38（`powercfg /h off`）の二重防御で、平日終日 kabu API 接続が落ちずに維持できることを確認
- 5/14 観測の「14:32 セッション断」のような中断は本日発生せず

### 残課題（持ち越し）
- **約定可能性を上げる施策**
  - 単価500円以下の銘柄を `auto_trade_stocks` に追加し、現残高10万円でも単元株が買える銘柄プールを確保
  - もしくは `investmentBudget` を実残高に合わせて手動で 100,000 円に下げ、設定上の予算と現実を一致させる
- **空売り未対応**: sell強度3の発火が日常的に14件規模で出ているが活用できていない（信用口座開設＋実装は中長期課題）
- kabu sendorder エラーレスポンス本文ログ化（Phase 39 残課題、本日500が出なかったため未着手）

### 変更ファイル
- なし（コード変更はゼロ、Phase 39 動作確認のみ）
