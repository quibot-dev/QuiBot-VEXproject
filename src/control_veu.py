import io
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
MODEL_SIZE = "base" # Model amb base de dades AIna per a català
debug = False
# ==========================================

# Inicialitzem el reproductor de fitxers MP3
pygame.mixer.init()

def reprodueix_resposta(fitxer_wav):
    """Reprodueix el so en segon pla sense congelar el robot"""
    try:
        ruta = os.path.join("audio", fitxer_wav)
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
    print("\n--- SISTEMA AIna DE VEU ACTIU ---")
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
                
                # --- ACCIONS I AUDIO-RESPOSTES ---
                if "esquerra" in text:
                    print("Movent safata cap a l'esquerra...")
                    print(">>> COMANDA: ENVIANT LEFT")
                    reprodueix_resposta("esquerra.wav")
                    if vex: 
                        vex.write(b"LEFT\n")
                        vex.flush()
                        
                elif "hola" in text or "bon dia" in text:
                    print("Hola!")
                    reprodueix_resposta("bondia.wav")

                elif "dreta" in text or "dret" in text:
                    print("Movent safata cap a la dreta...")
                    print(">>> COMANDA: ENVIANT RIGHT")
                    reprodueix_resposta("dreta.wav")
                    if vex:
                        vex.write(b"RIGHT\n")
                        vex.flush()
                     
                elif "puja" in text or "puj" in text:
                    print("Pujant el braç!")
                    print(">>> COMANDA: ENVIANT UP")
                    reprodueix_resposta("puja.wav")
                    if vex:
                        vex.write(b"UP\n")
                        vex.flush()

                elif "xucla" in text or "agaf" in text or "shukla" in text:
                    print("Xuclant el líquid amb la xeringa!")
                    print(">>> COMANDA: ENVIANT XUCLA")
                    reprodueix_resposta("xucla.wav")
                    if vex:
                        vex.write(b"XUCLA\n")
                        vex.flush()

                elif "buida" in text or "treu" in text or "bui" in text or "bóida" in text:
                    print("Deixant anar el líquid!")
                    print(">>> COMANDA: ENVIANT XTREU")
                    reprodueix_resposta("extreu.wav")
                    if vex:
                        vex.write(b"XTREU\n")
                        vex.flush()
                        
                elif "baix" in text or "baj" in text :
                    print("Baixant el braç!")
                    print(">>> COMANDA: ENVIANT DWN")
                    reprodueix_resposta("baixa.wav")
                    if vex: 
                        vex.write(b"DWN\n")
                        vex.flush()
                        
                elif "atura" in text or "par" in text or "a tu" in text or "stop" in text:
                    print("M'aturo!")
                    print(">>> COMANDA: ENVIANT STOP")
                    reprodueix_resposta("atura.wav")
                    if vex: 
                        vex.write(b"STOP\n")
                        vex.flush()

                elif "tont" in text or "estupid" in text:
                    print("Ei! Parlem-nos amb respecte.")
                    reprodueix_resposta("respecte.wav")

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