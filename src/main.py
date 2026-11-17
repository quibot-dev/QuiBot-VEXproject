# ---------------------------------------------------------------------------- #
#  VEX IQ GEN 2 (main.py) - v1.1 (límits del braç i control manual momentani)  #
# ---------------------------------------------------------------------------- #
from vex import *
import sys

# 1. CONFIGURACIÓ DE DISPOSITIUS
brain = Brain()
con = Controller() 

# Definim els motors als ports corresponents de la Gen 2
mot_cadena  = Motor(Ports.PORT4, False)
mot_brac    = Motor(Ports.PORT1, False)
mot_xeringa = Motor(Ports.PORT3, False)

# 2. LÍMITS DE SEGURETAT I PASSO-A-PASSO
XERINGA_MIN = 0
XERINGA_MAX = 200  

PAS_MIDA = 150       # Graus d'encoder per pas
CADENA_MIN_PAS = -3   # Màxim 3 passos esquerra
CADENA_MAX_PAS = 3    # Màxim 3 passos dreta

# v1.1: límits del braç (graus d'encoder respecte de la posició inicial).
# CAL CALIBRAR-LOS amb el robot real abans de fer-lo servir amb infants.
BRAC_MIN = -300
BRAC_MAX = 300

# Inicialització de posicions
mot_xeringa.set_position(0, DEGREES)
mot_cadena.set_position(0, DEGREES)
mot_brac.set_position(0, DEGREES)   # v1.1: referència per als límits del braç

# Variables globals
comanda_veu = ""
estat_brac = "PARAT"
estat_xeringa = "PARAT"
pas_actual = 0
target_cadena = 0
origen_brac = "VEU"      # v1.1: qui ha donat l'ordre del braç ("VEU" o "MANUAL")
origen_xeringa = "VEU"   # v1.1: el mateix per a la xeringa

boto_esq_premut_abans = False
boto_dreta_premut_abans = False

# 3. FIL DE FONS: Escolta el PC pel port USB-C (sys.stdin)
def escoltar_pc_veu():
    global comanda_veu
    while True:
        linia = sys.stdin.readline().strip().upper()
        if linia:
            comanda_veu = linia
        wait(20, MSEC)

fil_veu = Thread(escoltar_pc_veu)

brain.screen.clear_screen()
brain.screen.print("IQ GEN 2 LLEST")

# 4. BUCLE PRINCIPAL
while True:
    # --- PAS 1: ORDRES DE VEU ---
    if comanda_veu:
        if comanda_veu == "LEFT":    
            if pas_actual > CADENA_MIN_PAS:
                pas_actual -= 1
                target_cadena = pas_actual * PAS_MIDA
        elif comanda_veu == "RIGHT": 
            if pas_actual < CADENA_MAX_PAS:
                pas_actual += 1
                target_cadena = pas_actual * PAS_MIDA
        elif comanda_veu == "UP":    estat_brac, origen_brac = "PUJANT", "VEU"
        elif comanda_veu == "DWN":   estat_brac, origen_brac = "BAIXANT", "VEU"
        elif comanda_veu == "XUCLA": estat_xeringa, origen_xeringa = "XUCLANT", "VEU"
        elif comanda_veu == "XTREU": estat_xeringa, origen_xeringa = "BUIDANT", "VEU"
        elif comanda_veu == "STOP":
            estat_brac = estat_xeringa = "PARAT"
            target_cadena = mot_cadena.position(DEGREES)
            pas_actual = round(target_cadena / PAS_MIDA)
        comanda_veu = ""
    
    # --- PAS 2: BOTONS COMANDAMENT NATIUS DE VEX IQ ---
    # CORRECCIÓ: Mapeig correcte de la creueta de la Gen 2 (FUp = Esquerra, FDown = Dreta)
    prement_esq = con.buttonFUp.pressing()    
    prement_dret = con.buttonFDown.pressing() 

    # Detecció de flanc (només un pas per pulsació mecànica)
    if prement_esq and not boto_esq_premut_abans:
        if pas_actual > CADENA_MIN_PAS:
            pas_actual -= 1
            target_cadena = pas_actual * PAS_MIDA
            
    if prement_dret and not boto_dreta_premut_abans:
        if pas_actual < CADENA_MAX_PAS:
            pas_actual += 1
            target_cadena = pas_actual * PAS_MIDA

    boto_esq_premut_abans = prement_esq
    boto_dreta_premut_abans = prement_dret

    # Control del Braç amb els gallets esquerres de VEX IQ (buttonLUp / buttonLDown)
    # v1.1: el control manual només actua mentre el botó està premut
    if con.buttonLUp.pressing():     estat_brac, origen_brac = "PUJANT", "MANUAL"
    elif con.buttonLDown.pressing(): estat_brac, origen_brac = "BAIXANT", "MANUAL"
    elif origen_brac == "MANUAL":    estat_brac, origen_brac = "PARAT", "VEU"
        
    # Control de la Xeringa amb els gallets drets de VEX IQ (buttonRUp / buttonRDown)
    if con.buttonRUp.pressing():     estat_xeringa, origen_xeringa = "XUCLANT", "MANUAL"
    elif con.buttonRDown.pressing(): estat_xeringa, origen_xeringa = "BUIDANT", "MANUAL"
    elif origen_xeringa == "MANUAL": estat_xeringa, origen_xeringa = "PARAT", "VEU"

    # Botó de Pànic mecànic: Fletxa avall de la creueta frontal (CORREGIT a buttonEDown)
    if con.buttonEDown.pressing(): 
        estat_brac = estat_xeringa = "PARAT"
        target_cadena = mot_cadena.position(DEGREES)
        pas_actual = round(target_cadena / PAS_MIDA)
        target_cadena = pas_actual * PAS_MIDA

    # --- PAS 3: EXECUTAR MOVIMENTS ---
    
    # A) Xeringa
    pos_xeringa = mot_xeringa.position(DEGREES)
    if estat_xeringa == "XUCLANT" and pos_xeringa < XERINGA_MAX:
        mot_xeringa.spin(FORWARD, 15, PERCENT)
    elif estat_xeringa == "BUIDANT" and pos_xeringa > XERINGA_MIN:
        mot_xeringa.spin(REVERSE, 15, PERCENT)
    else:
        mot_xeringa.stop(HOLD) 
        if not (con.buttonRUp.pressing() or con.buttonRDown.pressing()):
            estat_xeringa = "PARAT"

    # B) Cadena (Moviment discret al 30% de velocitat per seguretat amb líquids)
    mot_cadena.spin_to_position(target_cadena, DEGREES, 30, PERCENT, False)

    # C) Braç (v1.1: amb límits, com la xeringa)
    pos_brac = mot_brac.position(DEGREES)
    if estat_brac == "PUJANT" and pos_brac < BRAC_MAX:
        mot_brac.spin(FORWARD, 15, PERCENT)
    elif estat_brac == "BAIXANT" and pos_brac > BRAC_MIN:
        mot_brac.spin(REVERSE, 15, PERCENT)
    else:
        mot_brac.stop(HOLD)
        estat_brac = "PARAT"

    wait(20, MSEC)