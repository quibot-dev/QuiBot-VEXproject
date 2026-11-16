"""Text-level test of the QuiBot-VEX command parser (control_veu.py).

Assumes a perfect transcription: it tests only how transcribed text is mapped
to commands, not speech recognition.
"""
import csv
import os
import re
from collections import Counter, defaultdict

MOVES = {"LEFT", "RIGHT", "UP", "DWN", "XUCLA", "XTREU", "STOP"}


def original(text):
    """Exact copy of the if/elif chain in control_veu.py."""
    text = text.strip().lower()
    if "esquerra" in text: return "LEFT"
    elif "hola" in text or "bon dia" in text: return "HELLO"
    elif "dreta" in text or "dret" in text: return "RIGHT"
    elif "puja" in text or "puj" in text: return "UP"
    elif "xucla" in text or "agaf" in text or "shukla" in text: return "XUCLA"
    elif "buida" in text or "treu" in text or "bui" in text or "bóida" in text: return "XTREU"
    elif "baix" in text or "baj" in text: return "DWN"
    elif "atura" in text or "par" in text or "a tu" in text or "stop" in text: return "STOP"
    elif "tont" in text or "estupid" in text: return "RESPECT"
    return "NONE"


def w(*words):
    return re.compile(r"\b(" + "|".join(words) + r")\b")


IMPROVED = [  # order matters: STOP first, for safety
    ("STOP", w("atura", "atura't", "aturat", "para", "parat", "prou", "stop", "quiet", "quieto")),
    ("LEFT", w("esquerra", "izquierda")),
    ("RIGHT", w("dreta", "derecha")),
    ("UP", w("puja", "pujar", "amunt", "aixeca", "sube", "arriba")),
    ("DWN", w("baixa", "baixar", "avall", "baja", "abajo")),
    ("XUCLA", w("xucla", "xuclar", "shukla", "aspira")),
    ("XTREU", w("buida", "buidar", "bóida", "deixa anar", "expulsa")),
    ("HELLO", w("hola", "bon dia", "bona tarda")),
    ("RESPECT", w("tonto", "tonta", "estúpid", "estúpida", "estupid", "imbècil")),
]


def improved(text):
    text = text.strip().lower()
    for token, pat in IMPROVED:
        if pat.search(text):
            return token
    return "NONE"


def evaluate(fn, rows):
    res = defaultdict(Counter)
    errors = []
    for r in rows:
        got = fn(r["text"])
        ok = got == r["expected"]
        res[r["group"]]["n"] += 1
        res[r["group"]]["ok"] += ok
        if r["group"] == "non_command" and got in MOVES:
            res["non_command"]["false_move"] += 1
        if not ok:
            errors.append((r["text"], r["expected"], got))
    return res, errors


if __name__ == "__main__":
  rows = list(csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "parser_corpus.csv"), encoding="utf-8")))
  for name, fn in [("original", original), ("improved", improved)]:
      res, errors = evaluate(fn, rows)
      print(f"\n=== {name} parser ===")
      for g in ["command", "social", "non_command"]:
          c = res[g]
          extra = f", unwanted movements: {c['false_move']}" if g == "non_command" else ""
          print(f"  {g:12s} correct {c['ok']}/{c['n']}{extra}")
      print("  errors:")
      for t, e, gtk in errors:
          print(f"    {t!r}: expected {e}, got {gtk}")
