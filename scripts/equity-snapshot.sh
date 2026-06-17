#!/bin/bash
# 「元手(=現金+保有評価額)」を1日1回スナップショットしてCSVに追記する。
# 月次の元手推移レポート用。kabu Stationが落ちている(残高取得不可)場合は何も書かずに終了する。
set -u

API="http://localhost:8734"
LOG_DIR="$HOME/.kabu-signal"
CSV="$LOG_DIR/equity-history.csv"
mkdir -p "$LOG_DIR"

# 残高(現金) + 保有評価額 を取得して合算。失敗時は exit 0 で記録しない(欠損は許容、誤データは残さない)。
python3 - "$API" "$CSV" <<'PY'
import sys, json, datetime, urllib.request

api, csv_path = sys.argv[1], sys.argv[2]

def get(path):
    with urllib.request.urlopen(f"{api}{path}", timeout=12) as r:
        return json.load(r)

try:
    bal = get("/api/brokerage/balance")
    if not isinstance(bal, dict) or "cashBalance" not in bal:
        sys.exit(0)  # kabu停止中など。記録しない。
    cash = float(bal.get("cashBalance") or 0)

    holdings = 0.0
    try:
        pos = get("/api/brokerage/positions")
        if isinstance(pos, list):
            for p in pos:
                holdings += float(p.get("currentPrice") or 0) * float(p.get("quantity") or 0)
    except Exception:
        pass  # 保有ゼロや一時失敗は0扱い

    today = datetime.date.today().isoformat()

    import os
    new = not os.path.exists(csv_path)
    # 同じ日に複数回走っても最後の1行で上書きしたいので、既存の当日行を除いて書き直す
    rows = []
    prev_cash = None  # 当日より前の最新行の現金(買付の現金反映遅れの検知に使う)
    if not new:
        with open(csv_path) as f:
            rows = [ln.rstrip("\n") for ln in f if ln.strip()]
        if rows and rows[0].startswith("date,"):
            header, rows = rows[0], rows[1:]
        else:
            header = "date,cash,holdings,total"
        rows = [r for r in rows if not r.startswith(today + ",")]
        for r in rows:  # rows は日付昇順・当日除外済みなので、当日より前の最新行=末尾側
            parts = r.split(",")
            if len(parts) >= 2 and parts[0] < today:
                try:
                    prev_cash = float(parts[1])
                except ValueError:
                    pass
    else:
        header = "date,cash,holdings,total"

    # --- 買付の現金反映遅れ補正 ---
    # kabu の cashBalance(=現物買付可能額) は当日の買付がT+2受渡まで控除されない一方、
    # /positions の保有株は即時計上されるため、その間 現金+保有 が買付額ぶん過大になる。
    # 取引履歴と突き合わせ、当日買付のうち現金にまだ反映されていない分だけ現金から控除する(下方向のみ=安全側)。
    try:
        txns = get("/api/transactions")
        if isinstance(txns, list) and prev_cash is not None:
            buys = sum(float(t.get("totalAmount") or 0) for t in txns
                       if t.get("transactionType") == "buy" and str(t.get("transactionDate", ""))[:10] == today)
            sells = sum(float(t.get("totalAmount") or 0) for t in txns
                        if t.get("transactionType") == "sell" and str(t.get("transactionDate", ""))[:10] == today)
            observed_drop = prev_cash + sells - cash  # 売却ぶんを除いた実際の現金減少
            unreflected = buys - observed_drop        # 買付額のうちまだ控除されていない分
            if unreflected > 1:
                cash -= unreflected
                print(f"adjust: 未反映の買付 ¥{int(unreflected)} を控除 "
                      f"(cash {int(cash + unreflected)}→{int(cash)})", file=sys.stderr)
    except Exception as e:
        print(f"adjust-skip: {e}", file=sys.stderr)

    total = cash + holdings

    rows.append(f"{today},{int(cash)},{int(holdings)},{int(total)}")
    with open(csv_path, "w") as f:
        f.write(header + "\n" + "\n".join(rows) + "\n")
    print(f"snapshot {today}: cash={int(cash)} holdings={int(holdings)} total={int(total)}")
except Exception as e:
    print(f"skip: {e}", file=sys.stderr)
    sys.exit(0)
PY
