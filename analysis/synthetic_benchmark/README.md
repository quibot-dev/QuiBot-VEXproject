# Prova amb veus sintètiques

Mesura com reconeix les ordres el model Whisper `base` (el mateix que fa servir el robot) sense necessitat de participants:

- **Frases:** les 53 de `../parser_corpus.csv` (28 ordres, 5 salutacions o insults i 20 frases que no són ordres).
- **Veus:** dues veus sintètiques catalanes del projecte Piper, `upc_ona` (dona, qualitat mitjana) i `upc_pau` (home, qualitat baixa), a velocitat normal i a 1,2×.
- **Soroll:** veus de fons en català, com en una aula, a 20, 10 i 5 dB, més la condició en silenci.
- **Reconeixement:** Whisper `base`, quantitzat a 8 bits, descodificació voraç, català; executat amb sherpa-onnx.
- **Total:** 848 transcripcions.

| Fitxer | Contingut |
|---|---|
| `run_benchmark.py` | Executa la prova i en mostra el resum |
| `results.csv` | Les transcripcions exactes que es presenten a l'article |
| `babble.npy` | La pista de veus de fons que es va fer servir |

```bash
pip install "sherpa-onnx==1.12.40" numpy scipy
python run_benchmark.py --summary   # resum dels resultats de l'article
python run_benchmark.py             # nova execució (afegeix files a results.csv)
```

Les veus sintètiques són més clares que les dels infants: els resultats són una estimació optimista. La síntesi de veu té una part aleatòria, de manera que una nova execució dona resultats semblants, però no idèntics.
