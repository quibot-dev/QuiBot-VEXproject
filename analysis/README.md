# Scripts de l'article

| Script | Què fa | Com s'executa |
|---|---|---|
| `parser_test.py` | Prova com es converteix el text transcrit en ordres, amb les 53 frases de `parser_corpus.csv`, comparant el codi original i el millorat | `python parser_test.py` |
| `sim.py` | Executa `src/main.py` sense modificar amb motors i comandament simulats (sis escenaris) | `python sim.py` |
| `synthetic_benchmark/run_benchmark.py` | Prova amb veus sintètiques catalanes i soroll de fons (848 transcripcions); vegeu `synthetic_benchmark/README.md` | `python synthetic_benchmark/run_benchmark.py --summary` |
| `voice_tests/measure_voice.py` | Prova de veu amb persones a l'ordinador: desa què entén el model i quant triga | `python voice_tests/measure_voice.py --speaker S1 --condition silenci --model base` |
| `voice_tests/analyze_voice.py` | Resumeix els resultats de la prova de veu | `python voice_tests/analyze_voice.py` |

`parser_test.py` i `sim.py` no necessiten el robot ni el micròfon. Els resultats de l'article s'han obtingut amb la versió `v1.0-juny2026` de `src/main.py`.
