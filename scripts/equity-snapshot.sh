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

    total = cash + holdings
    today = datetime.date.today().isoformat()

    import os
    new = not os.path.exists(csv_path)
    # 同じ日に複数回走っても最後の1行で上書きしたいので、既存の当日行を除いて書き直す
    rows = []
    if not new:
        with open(csv_path) as f:
            rows = [ln.rstrip("\n") for ln in f if ln.strip()]
        if rows and rows[0].startswith("date,"):
            header, rows = rows[0], rows[1:]
        else:
            header = "date,cash,holdings,total"
        rows = [r for r in rows if not r.startswith(today + ",")]
    else:
        header = "date,cash,holdings,total"

    rows.append(f"{today},{int(cash)},{int(holdings)},{int(total)}")
    with open(csv_path, "w") as f:
        f.write(header + "\n" + "\n".join(rows) + "\n")
    print(f"snapshot {today}: cash={int(cash)} holdings={int(holdings)} total={int(total)}")
except Exception as e:
    print(f"skip: {e}", file=sys.stderr)
    sys.exit(0)
PY
