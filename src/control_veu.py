import io
import re
import os
import serial
import serial.tools.list_ports  # <--- Nova llibreria per escanejar ports
import time
import speech_recognition as sr
from faster_whisper import WhisperModel

# Desactivem logs de Pygame per netejar la consola
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

# ==========================================
#         CONFIGURACIÓ AUTOMÀTICA
# ==========================================
MODEL_SIZE = "base"  # Model multilingüe de Whisper; el català es fixa a transcribe(language="ca")


# --- v1.1: RECONEIXEMENT D'ORDRES PER PARAULES SENCERES ---
# L'ordre de la llista importa: l'aturada va primer, per seguretat.
def _paraules(*p):
    return re.compile(r"\b(" + "|".join(p) + r")\b")

REGLES = [
    ("STOP",    _paraules("atura", "atura't", "aturat", "para", "parat", "prou", "stop", "quiet", "quieto")),
    ("LEFT",    _paraules("esquerra", "izquierda")),
    ("RIGHT",   _paraules("dreta", "derecha")),
    ("UP",      _paraules("puja", "pujar", "amunt", "aixeca", "sube", "arriba")),
    ("DWN",     _paraules("baixa", "baixar", "avall", "baja", "abajo")),
    ("XUCLA",   _paraules("xucla", "xuclar", "shukla", "aspira")),
    ("XTREU",   _paraules("buida", "buidar", "bóida", "deixa anar", "expulsa")),
    ("HELLO",   _paraules("hola", "bon dia", "bona tarda")),
    ("RESPECT", _paraules("tonto", "tonta", "estúpid", "estúpida", "estupid", "imbècil")),
]

def interpreta(text):
    text = text.strip().lower()
    for ordre, patro in REGLES:
        if patro.search(text):
            return ordre
    return None

# ordre -> (missatge a la consola, àudio de resposta, token per al VEX o None)
ACCIONS = {
    "LEFT":    ("Movent la safata cap a l'esquerra...", "esquerra.wav", "LEFT"),
    "RIGHT":   ("Movent la safata cap a la dreta...", "dreta.wav", "RIGHT"),
    "UP":      ("Pujant el braç!", "puja.wav", "UP"),
    "DWN":     ("Baixant el braç!", "baixa.wav", "DWN"),
    "XUCLA":   ("Xuclant el líquid amb la xeringa!", "xucla.wav", "XUCLA"),
    "XTREU":   ("Deixant anar el líquid!", "extreu.wav", "XTREU"),
    "STOP":    ("M'aturo!", "atura.wav", "STOP"),
    "HELLO":   ("Hola!", "bondia.wav", None),
    "RESPECT": ("Ei! Parlem-nos amb respecte.", "respecte.wav", None),
}
debug = False
# ==========================================

# Inicialitzem el reproductor de fitxers MP3
pygame.mixer.init()

def reprodueix_resposta(fitxer_wav):
    """Reprodueix el so en segon pla sense congelar el robot"""
    try:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_interface", fitxer_wav)
        if os.path.exists(ruta):
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.play()
        else:
            print(f"Avís: No s'ha trobat l'àudio a: {ruta}")
    except Exception as e:
        print(f"Error àudio: {e}")

# Carreguem el cervell de l'IA
print(f"Carregant Whisper ({MODEL_SIZE}) amb optimització en català...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

# ==========================================
#    SISTEMA DE DETECCIÓ AUTOMÀTICA DE PORT
# ==========================================
print("\nBuscant connexió amb el robot VEX...")
ports_disponibles = list(serial.tools.list_ports.comports())
vex = None

if not ports_disponibles:
    print("AVÍS: No s'ha detectat cap dispositiu USB/Sèrie connectat. Mode simulació actiu.")
else:
    for p in ports_disponibles:
        try:
            print(f"Provant de connectar a {p.device} ({p.description})...")
            # Intentem obrir el port detectat
            vex = serial.Serial(p.device, 115200, timeout=1)
            print(f"-> ¡CONNECTAT CORRECTAMENT AL VEX A {p.device}!")
            time.sleep(2) # Seguretat per inicialitzar el port
            break # Si funciona, sortim del bucle i ens quedem amb aquest port
        except Exception:
            # Si dona error (està ocupat o no és el robot), continuem provant el següent
            vex = None
            continue

    if vex is None:
        print("AVÍS: S'han trobat ports USB, però cap estava lliure o disponible. Mode simulació actiu.")
# ==========================================

# Configurar micròfon
r = sr.Recognizer()
mic = sr.Microphone()

with mic as source:
    print("\nCalibrant soroll ambiental de la sala...")
    r.adjust_for_ambient_noise(source, duration=1)
    print("\n--- SISTEMA DE VEU ACTIU (Whisper, català, sense connexió) ---")
    print("Digues clarament: 'Esquerra', 'Dreta','Atura'...")

    while True:
        try:
            print("\nEscoltant...")
            # Capturem talls de veu de màxim 3 segons per evitar lag
            audio = r.listen(source, phrase_time_limit=3)
            
            # Passem l'àudio directament per memòria (més ràpid)
            wav_data = io.BytesIO(audio.get_wav_data())
            segments, _ = model.transcribe(wav_data, language="ca", beam_size=1)
            
            for segment in segments:
                text = segment.text.strip().lower()
                if debug == True:
                    print(f"He entès: \"{text}\"")
                
                # --- ACCIONS I AUDIO-RESPOSTES (v1.1) ---
                # Paraules senceres; l'aturada es comprova primer, per seguretat.
                ordre = interpreta(text)
                if ordre in ACCIONS:
                    missatge, wav, token = ACCIONS[ordre]
                    print(missatge)
                    reprodueix_resposta(wav)
                    if token:
                        print(f">>> COMANDA: ENVIANT {token}")
                        if vex:
                            vex.write((token + "\n").encode())
                            vex.flush()
                else:
                    print("Crec que no t'he acabat d'entendre, m'ho podries repetir si us plau?")
                    reprodueix_resposta("repetir.wav")        

        except sr.UnknownValueError:
            # Si només detecta un copet o soroll de fons, continua escoltant
            pass
        except KeyboardInterrupt:
            print("\nAturant el sistema de veu de Windows...")
            if vex: vex.close()
            break
        except Exception as e:
            print(f"Error en el bucle: {e}")