"""Synthetic-voice benchmark of QuiBot-VEX speech recognition (no participants needed).

Synthesizes the 53 utterances of ../parser_corpus.csv with two Catalan Piper voices
(upc_ona, medium quality; upc_pau, low quality) at speeds 1.0 and 1.2, mixes them with
overlapping Catalan speech (babble) at 20, 10 and 5 dB SNR, transcribes every clip with
Whisper base (int8, greedy decoding, language "ca") through sherpa-onnx, and maps each
transcript to a command with the original and the improved parser (848 transcriptions).

Usage:
    pip install "sherpa-onnx==1.12.40" numpy scipy
    python run_benchmark.py                # all utterances
    python run_benchmark.py 0 10           # optional: utterances 0-9 only (resumable)
    python run_benchmark.py --summary      # print the summary table of results.csv
Models are downloaded automatically from the sherpa-onnx GitHub releases.

Reproducibility: speech synthesis with Piper (VITS) is stochastic, so a new run gives
slightly different transcriptions, especially with noise, but similar aggregate results.
results.csv contains the exact transcriptions reported in the article, and babble.npy the
exact background-speech track used. Running the script appends new rows to results.csv:
rename it first if you want to keep the original.
"""
import csv, os, sys, tarfile, time, urllib.request
from collections import defaultdict
from math import gcd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from parser_test import original, improved  # noqa: E402

MODELS = os.path.join(HERE, "models")
RESULTS = os.path.join(HERE, "results.csv")
BASE_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
ARCHIVES = {"sherpa-onnx-whisper-base": "asr-models/sherpa-onnx-whisper-base.tar.bz2",
            "vits-piper-ca_ES-upc_ona-medium": "tts-models/vits-piper-ca_ES-upc_ona-medium.tar.bz2",
            "vits-piper-ca_ES-upc_pau-x_low": "tts-models/vits-piper-ca_ES-upc_pau-x_low.tar.bz2"}
MOVES = {"LEFT", "RIGHT", "UP", "DWN", "XUCLA", "XTREU", "STOP"}
NOISES = [None, 20, 10, 5]
SPEEDS = [1.0, 1.2]
BABBLE = ["Mira com canvia de color", "Ara em toca a mi", "On és la peça blava?", "Jo ho vull provar",
          "Quin color tindrà l'aigua?", "Ajuda'm amb aquesta peça", "Ja està muntat",
          "Encara falta la cadena", "Que divertit!", "Escolteu un moment"]


def fetch_models():
    os.makedirs(MODELS, exist_ok=True)
    for name, path in ARCHIVES.items():
        if not os.path.isdir(os.path.join(MODELS, name)):
            arc = os.path.join(MODELS, os.path.basename(path))
            print("Downloading", path)
            urllib.request.urlretrieve(BASE_URL + path, arc)
            with tarfile.open(arc) as t:
                t.extractall(MODELS)
            os.remove(arc)


def make_tts(name):
    import glob
    import sherpa_onnx
    d = os.path.join(MODELS, f"vits-piper-ca_ES-upc_{name}")
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=glob.glob(f"{d}/*.onnx")[0],
                                                   tokens=f"{d}/tokens.txt", data_dir=f"{d}/espeak-ng-data"),
        num_threads=4))
    return sherpa_onnx.OfflineTts(cfg)


def synth16(tts, text, speed=1.0):
    from scipy.signal import resample_poly
    a = tts.generate(text, sid=0, speed=speed)
    x = np.array(a.samples, dtype=np.float32)
    g = gcd(16000, a.sample_rate)
    return resample_poly(x, 16000 // g, a.sample_rate // g).astype(np.float32)


def make_asr():
    import sherpa_onnx
    d = os.path.join(MODELS, "sherpa-onnx-whisper-base")
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=f"{d}/base-encoder.int8.onnx", decoder=f"{d}/base-decoder.int8.onnx",
        tokens=f"{d}/base-tokens.txt", language="ca", task="transcribe",
        num_threads=4, decoding_method="greedy_search")


def transcribe(asr, x):
    s = asr.create_stream()
    s.accept_waveform(16000, x)
    asr.decode_stream(s)
    return s.result.text.strip()


def babble_track(voices):
    path = os.path.join(HERE, "babble.npy")
    if os.path.exists(path):
        return np.load(path)
    rng = np.random.default_rng(7)
    streams = []
    for _ in range(4):
        seq = []
        for s in rng.permutation(BABBLE):
            v = voices["ona" if rng.random() < .5 else "pau"]
            seq += [synth16(v, s), np.zeros(int(16000 * rng.uniform(.1, .4)), np.float32)]
        streams.append(np.concatenate(seq))
    n = min(len(s) for s in streams)
    b = sum(s[:n] for s in streams)
    b /= np.sqrt(np.mean(b ** 2))
    np.save(path, b)
    return b


def mix(x, snr, babble, rng):
    if snr is None:
        return x
    start = rng.integers(0, len(babble) - len(x) - 1) if len(babble) > len(x) + 1 else 0
    n = np.resize(babble[start:start + len(x)], len(x))
    return (x + n * np.sqrt(np.mean(x ** 2) / (10 ** (snr / 10)))).astype(np.float32)


def run(start, end):
    fetch_models()
    rows = list(csv.DictReader(open(os.path.join(os.path.dirname(HERE), "parser_corpus.csv"), encoding="utf-8")))
    voices = {"ona": make_tts("ona-medium"), "pau": make_tts("pau-x_low")}
    babble = babble_track(voices)
    asr = make_asr()
    pad = np.zeros(int(0.3 * 16000), np.float32)
    new = not os.path.exists(RESULTS)
    with open(RESULTS, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["voice", "speed", "noise", "group", "text", "expected", "transcript",
                        "original_parser", "improved_parser", "transcription_s", "audio_s"])
        for i, r in enumerate(rows[start:end], start):
            rng = np.random.default_rng(1000 + i)
            for vn, v in voices.items():
                for sp in SPEEDS:
                    x = np.concatenate([pad, synth16(v, r["text"], sp), pad])
                    for snr in NOISES:
                        y = mix(x, snr, babble, rng)
                        t0 = time.perf_counter()
                        t = transcribe(asr, y)
                        w.writerow([vn, sp, "clean" if snr is None else f"babble{snr}", r["group"], r["text"],
                                    r["expected"], t, original(t), improved(t),
                                    f"{time.perf_counter() - t0:.3f}", f"{len(y) / 16000:.2f}"])
            f.flush()
            print(f"{i + 1}/{len(rows)}", flush=True)


def summary():
    rows = list(csv.DictReader(open(RESULTS, encoding="utf-8")))
    print("noise      parser    commands      unwanted movements")
    for n in ["clean", "babble20", "babble10", "babble5"]:
        rs = [r for r in rows if r["noise"] == n]
        cmd = [r for r in rs if r["group"] == "command"]
        non = [r for r in rs if r["group"] == "non_command"]
        for p in ("original_parser", "improved_parser"):
            c = sum(r[p] == r["expected"] for r in cmd)
            b = sum(r[p] in MOVES for r in non)
            pc = f"{100 * c / len(cmd):4.1f}%" if cmd else "  - "
            pb = f"{100 * b / len(non):4.1f}%" if non else "  - "
            print(f"{n:10s} {p[:8]:9s} {c:3d}/{len(cmd)} ({pc})  {b:3d}/{len(non)} ({pb})")
    tok = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["group"] == "command":
            tok[r["expected"]][0] += 1
            tok[r["expected"]][1] += r["improved_parser"] == r["expected"]
    print("\nper command (improved parser):", {k: f"{100 * v[1] / v[0]:.0f}%" for k, v in sorted(tok.items())})


if __name__ == "__main__":
    if "--summary" in sys.argv:
        summary()
    else:
        a = [int(x) for x in sys.argv[1:3]] if len(sys.argv) >= 3 else [0, 10 ** 6]
        run(*a)
        summary()
