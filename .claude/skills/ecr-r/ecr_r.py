#!/usr/bin/env python3
"""ECR-R session helper: question order, answer recording, and scoring.

Usage:
  ecr_r.py start [--seed N]        new session with a randomized question order
  ecr_r.py next                    print the next unanswered question
  ecr_r.py record ITEM VALUE       save an answer (ITEM 1-36, VALUE 1-7)
  ecr_r.py score                   score the session (needs all 36 answers)

The session is kept in .ecr-r-session.json in the current directory.
"""
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSION = Path.cwd() / ".ecr-r-session.json"
ITEMS = json.loads((HERE / "items.json").read_text(encoding="utf-8"))
BY_N = {it["n"]: it for it in ITEMS["items"]}


def load():
    if not SESSION.exists():
        sys.exit("没有进行中的测试，先运行: ecr_r.py start")
    return json.loads(SESSION.read_text(encoding="utf-8"))


def save(s):
    SESSION.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def start(args):
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else random.randrange(10**9)
    order = list(BY_N)
    random.Random(seed).shuffle(order)
    save({"seed": seed, "order": order, "answers": {}})
    print(f"新测试已开始（随机顺序种子 {seed}），共 36 题。")


def next_q(_):
    s = load()
    pending = [n for n in s["order"] if str(n) not in s["answers"]]
    if not pending:
        print("36 题已全部作答，运行: ecr_r.py score")
        return
    n = pending[0]
    done = 36 - len(pending)
    it = BY_N[n]
    print(f"第 {done + 1}/36 题（原题号 {n}）")
    print(it["zh"])
    print(f"[原文] {it['en']}")


def record(args):
    n, v = int(args[0]), int(args[1])
    if n not in BY_N or not 1 <= v <= 7:
        sys.exit("题号须为 1-36，分值须为 1-7")
    s = load()
    s["answers"][str(n)] = v
    save(s)
    print(f"已记录：第 {n} 题 = {v}（已答 {len(s['answers'])}/36）")


def score(_):
    s = load()
    missing = [n for n in BY_N if str(n) not in s["answers"]]
    if missing:
        sys.exit(f"还有 {len(missing)} 题未答：{missing}")
    result = {}
    for sub in ("anxiety", "avoidance"):
        rows = []
        for it in ITEMS["items"]:
            if it["subscale"] != sub:
                continue
            raw = s["answers"][str(it["n"])]
            rows.append((it["n"], raw, 8 - raw if it["reverse"] else raw, it["reverse"]))
        total = sum(r[2] for r in rows)
        result[sub] = {"rows": rows, "sum": total, "mean": round(total / 18, 2)}

    names = {"anxiety": "依恋焦虑", "avoidance": "依恋回避"}
    for sub in ("avoidance", "anxiety"):
        r = result[sub]
        print(f"\n== {names[sub]}（{sub}）==")
        print("题号  作答  计分")
        for n, raw, scored, rev in r["rows"]:
            print(f"{n:>4}  {raw:>4}  {scored:>4}{'  (反向)' if rev else ''}")
        print(f"18 题合计：{r['sum']}（范围 18–126）")
        print(f"平均分：{r['mean']:.2f}（范围 1.00–7.00，越高越不安全）")
    s["result"] = {k: {"sum": v["sum"], "mean": v["mean"]} for k, v in result.items()}
    save(s)


COMMANDS = {"start": start, "next": next_q, "record": record, "score": score}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    COMMANDS[sys.argv[1]](sys.argv[2:])
