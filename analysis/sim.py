"""Software-in-the-loop simulation of the VEX IQ Brain program (src/main.py).

Runs the unmodified control program against simulated motors and controller.
Motors are modeled kinematically: speed% of a 120 rpm motor (720 deg/s at 100%).
Usage: python sim.py
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "..", "src", "main.py")

def _build_source():
    src = open(MAIN, encoding="utf-8").read().replace("\r", "")
    src = src.replace("from vex import *", "")
    src = src.replace("fil_veu = Thread(escoltar_pc_veu)", "")
    src = src.replace("# 4. BUCLE PRINCIPAL\nwhile True:",
                      "# 4. BUCLE PRINCIPAL\nfor _tick in range(N_TICKS):\n    _hook(_tick, globals())")
    assert "_hook(_tick" in src, "main.py structure changed: update sim.py"
    return src

SIM_SOURCE = _build_source()

DT=0.020; MAXDPS=720.0
DEGREES='deg'; PERCENT='pct'; MSEC='ms'; FORWARD=1; REVERSE=-1; HOLD='hold'; BRAKE='brake'
class Ports: PORT1='P1'; PORT3='P3'; PORT4='P4'
class Motor:
    def __init__(s,port,rev=False): s.pos=0.0; s.vel=0.0; s.target=None; s.tspeed=0
    def set_position(s,v,u): s.pos=float(v)
    def position(s,u): return s.pos
    def spin(s,d,speed,u): s.vel=d*speed/100*MAXDPS; s.target=None
    def stop(s,mode=HOLD): s.vel=0.0; s.target=None
    def spin_to_position(s,t,u,speed,u2,wait=True): s.target=float(t); s.tspeed=speed/100*MAXDPS
    def step(s):
        if s.target is not None:
            d=s.target-s.pos; m=s.tspeed*DT
            s.pos = s.target if abs(d)<=m else s.pos+m*(1 if d>0 else -1)
        else: s.pos+=s.vel*DT
class Btn:
    def __init__(s): s.p=False
    def pressing(s): return s.p
class Controller:
    def __init__(s):
        for n in ['buttonFUp','buttonFDown','buttonLUp','buttonLDown','buttonRUp','buttonRDown','buttonEDown']: setattr(s,n,Btn())
class Screen:
    def clear_screen(s): pass
    def print(s,*a): pass
class Brain:
    def __init__(s): s.screen=Screen()
def wait(v,u): pass
def Thread(f): return None
import sys

def run(name, seconds, voice=None, buttons=None):
    """voice: {time_s: token}; buttons: {(t0,t1): button_name}"""
    voice=voice or {}; buttons=buttons or {}
    ns={k:v for k,v in globals().items()}
    ns['N_TICKS']=int(seconds/DT)
    log=[]
    def hook(tick,g):
        t=tick*DT
        for tv,tok in voice.items():
            if abs(t-tv)<DT/2: g['comanda_veu']=tok
        for (t0,t1),b in buttons.items():
            getattr(g['con'],b).p = (t0<=t<t1)
        if tick>0:
            for m in ('mot_cadena','mot_brac','mot_xeringa'): g[m].step()
        log.append((round(t,2),round(g['mot_cadena'].pos,1),round(g['mot_brac'].pos,1),round(g['mot_xeringa'].pos,1),g['estat_brac'],g['estat_xeringa'],g['pas_actual']))
    ns['_hook']=hook
    exec(SIM_SOURCE, ns)
    return log

def show(name,log,every=None):
    last=log[-1]
    print(f"\n[{name}] final: conveyor={last[1]} deg, arm={last[2]} deg, syringe={last[3]} deg, arm_state={last[4]}, syringe_state={last[5]}, step={last[6]}")

# S1: five RIGHT commands -> capped at 3 steps (450 deg)
L=run("S1",3,voice={0.1:'RIGHT',0.3:'RIGHT',0.5:'RIGHT',0.7:'RIGHT',0.9:'RIGHT'}); show("S1 five RIGHT commands",L)
# S2: XUCLA -> syringe stops at its limit
L=run("S2",4,voice={0.1:'XUCLA'}); show("S2 XUCLA",L)
t_full=next(r[0] for r in L if r[3]>=200); print(f"   syringe reached 200 deg at t={t_full} s (command at 0.1 s)")
# S3: XUCLA then panic button at 0.6 s
L=run("S3",3,voice={0.1:'XUCLA'},buttons={(0.6,0.7):'buttonEDown'}); show("S3 XUCLA + panic button",L)
# S4: UP for 10 s with no further command -> no arm limit
L=run("S4",10,voice={0.1:'UP'}); show("S4 UP and no STOP for 10 s",L)
# S5: voice UP and manual 'arm down' in the same tick
L=run("S5",1,voice={0.10:'UP'},buttons={(0.10,0.5):'buttonLDown'}); 
st=[r for r in L if r[0]==0.12][0]; print(f"\n[S5 voice UP + manual DOWN same tick] arm_state at 0.12 s = {st[4]}; final arm={L[-1][2]} deg")
# S6: STOP while conveyor moving -> target snaps to nearest step
L=run("S6",2,voice={0.1:'RIGHT',0.25:'STOP'}); show("S6 RIGHT then STOP mid-move",L)
