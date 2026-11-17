"""Held-out test of the command parsers with utterances not used to design them.

Usage: python heldout_test.py
"""
import csv, os
from parser_test import original, improved

HERE = os.path.dirname(os.path.abspath(__file__))
MOVES = {"LEFT", "RIGHT", "UP", "DWN", "XUCLA", "XTREU", "STOP"}
rows = list(csv.DictReader(open(os.path.join(HERE, "heldout_corpus.csv"), encoding="utf-8")))
for name, fn in [("original", original), ("improved", improved)]:
    cmd = [r for r in rows if r["group"] == "command"]
    non = [r for r in rows if r["group"] == "non_command"]
    soc = [r for r in rows if r["group"] == "social"]
    print(f"\n{name}: commands {sum(fn(r['text']) == r['expected'] for r in cmd)}/{len(cmd)}, "
          f"greetings and insults {sum(fn(r['text']) == r['expected'] for r in soc)}/{len(soc)}, "
          f"non-commands that move the robot {sum(fn(r['text']) in MOVES for r in non)}/{len(non)}")
    for r in cmd + non:
        got = fn(r["text"])
        if (r["group"] == "command" and got != r["expected"]) or (r["group"] == "non_command" and got in MOVES):
            print(f"   {r['text']!r}: expected {r['expected']}, got {got}")
