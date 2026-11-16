"""Measure command recognition and host-side latency of QuiBot-VEX voice control.

Run on the computer that controls the robot, from the folder of control_veu.py:
    python measure_voice.py --speaker S1 --condition quiet --model base
The script shows a phrase, you say it, and it records what Whisper understood,
which command each parser produces, and how long transcription took.
Results are appended to voice_results.csv. The robot does not need to be connected.
"""
import argparse, csv, io, random, time, os
import speech_recognition as sr
from faster_whisper import WhisperModel
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parser_test import original, improved

PROMPTS = [  # (phrase, expected command)
    ("Esquerra", "LEFT"), ("Cap a la dreta", "RIGHT"), ("Puja el braç", "UP"), ("Baixa el braç", "DWN"),
    ("Xucla el líquid", "XUCLA"), ("Buida la xeringa", "XTREU"), ("Atura't", "STOP"), ("Para", "STOP"),
    ("Ara parlarem de química", "NONE"), ("Preparem la dissolució", "NONE"), ("Mira aquest aparell", "NONE"),
    ("Tinc una pregunta", "NONE"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--speaker", required=True); ap.add_argument("--condition", required=True)
ap.add_argument("--model", default="base"); ap.add_argument("--reps", type=int, default=3)
a = ap.parse_args()

print(f"Loading Whisper model '{a.model}'...")
model = WhisperModel(a.model, device="cpu", compute_type="int8")
r = sr.Recognizer(); mic = sr.Microphone()
items = PROMPTS * a.reps; random.shuffle(items)
new = not os.path.exists("voice_results.csv")
with mic as source, open("voice_results.csv", "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["speaker", "condition", "model", "phrase", "expected", "transcript",
                    "original_parser", "improved_parser", "transcription_s", "pause_threshold_s"])
    r.adjust_for_ambient_noise(source, duration=1)
    for i, (phrase, expected) in enumerate(items, 1):
        input(f"\n[{i}/{len(items)}] Prem Enter i digues: «{phrase}»")
        audio = r.listen(source, phrase_time_limit=3)
        t0 = time.perf_counter()
        segments, _ = model.transcribe(io.BytesIO(audio.get_wav_data()), language="ca", beam_size=1)
        text = " ".join(s.text.strip() for s in segments).strip()
        dt = time.perf_counter() - t0
        print(f"   ha entès: «{text}»  ({dt:.2f} s)")
        w.writerow([a.speaker, a.condition, a.model, phrase, expected, text,
                    original(text), improved(text), f"{dt:.3f}", r.pause_threshold]); f.flush()
print("\nDone. Results in voice_results.csv")
