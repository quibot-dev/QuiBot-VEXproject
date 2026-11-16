"""Summarize voice_results.csv: accuracy per model, condition and parser, and latency."""
import csv, statistics
from collections import defaultdict
rows = list(csv.DictReader(open("voice_results.csv", encoding="utf-8")))
MOVES = {"LEFT", "RIGHT", "UP", "DWN", "XUCLA", "XTREU", "STOP"}
groups = defaultdict(list)
for r in rows: groups[(r["model"], r["condition"])].append(r)
for (m, c), g in sorted(groups.items()):
    cmd = [r for r in g if r["expected"] != "NONE"]; non = [r for r in g if r["expected"] == "NONE"]
    print(f"\nModel {m}, {c} (n={len(g)}, speakers={len({r['speaker'] for r in g})})")
    for p in ("original_parser", "improved_parser"):
        acc = sum(r[p] == r["expected"] for r in cmd) / max(len(cmd), 1)
        fa = sum(r[p] in MOVES for r in non) / max(len(non), 1)
        print(f"  {p:16s} commands correct {100*acc:.0f}%   unwanted movements on non-commands {100*fa:.0f}%")
    t = sorted(float(r["transcription_s"]) for r in g); pt = float(g[0]["pause_threshold_s"])
    med = statistics.median(t); p90 = t[int(0.9 * (len(t) - 1))]
    print(f"  transcription median {med:.2f} s, p90 {p90:.2f} s -> estimated end-of-speech to command: {pt+med+0.04:.2f} s (median)")
