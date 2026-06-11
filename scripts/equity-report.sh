#!/bin/bash
# 元手スナップショットCSVから「先月→今月の増減」を集計して表示する。月次報告用。
set -u
CSV="$HOME/.kabu-signal/equity-history.csv"

python3 - "$CSV" <<'PY'
import sys, csv, datetime, os
path = sys.argv[1]
if not os.path.exists(path):
    print("まだ記録がありません(初回は翌営業日15:05以降)"); sys.exit(0)

rows = []
with open(path) as f:
    for r in csv.DictReader(f):
        try:
            rows.append((datetime.date.fromisoformat(r["date"]), int(r["total"]),
                         int(r["cash"]), int(r["holdings"])))
        except Exception:
            pass
if not rows:
    print("有効なデータがありません"); sys.exit(0)
rows.sort()

start_d, start_t, _, _ = rows[0]      # 記録開始(基準)
last_d, last_t, last_c, last_h = rows[-1]  # 最新

# 当月の最初の記録
this_month = [r for r in rows if (r[0].year, r[0].month) == (last_d.year, last_d.month)]
m_start_d, m_start_t = this_month[0][0], this_month[0][1]

def line(label, d, t): print(f"  {label}: {d}  元手 ¥{t:,}")

print("=== 元手の推移 ===")
line("記録開始", start_d, start_t)
line("今月初め", m_start_d, m_start_t)
line("最新   ", last_d, last_t)
print(f"    (内訳: 現金 ¥{last_c:,} / 保有 ¥{last_h:,})")
print()
mo = last_t - m_start_t
al = last_t - start_t
sign = lambda x: ("+" if x >= 0 else "") + f"¥{x:,}"
pct = lambda b, x: f"({sign_pct(x/b*100)})" if b else ""
def sign_pct(p): return ("+" if p >= 0 else "") + f"{p:.1f}%"
print(f"今月の増減 : {sign(mo)} {pct(m_start_t, mo)}")
print(f"開始来の増減: {sign(al)} {pct(start_t, al)}")
PY
