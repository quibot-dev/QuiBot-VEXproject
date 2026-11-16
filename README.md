# QuiBot-VEX: robot de química controlat per veu en català

Robot de manipulació de líquids per a activitats de química amb infants, construït amb **VEX IQ (2a generació)** i controlat amb **ordres de veu en català**, reconegudes **sense connexió a internet** en un ordinador. Forma part del Projecte QuiBot (UPC).

🌐 Lloc web del projecte: https://quibot.upc.edu/

*English: a liquid-handling chemistry robot built with VEX IQ (2nd generation) and controlled with Catalan voice commands, recognized offline on a computer with a quantized Whisper model.*

## 📁 Estructura del repositori

| Carpeta | Contingut |
|---|---|
| `src/main.py` | Programa del VEX IQ Brain (Python): bucle de control de 20 ms, límits de la xeringa i de la safata, prioritat del comandament i botó d'aturada |
| `src/control_veu.py` | Programa de l'ordinador: captura d'àudio, reconeixement de veu (Whisper `base`, int8, català), conversió en ordres i enviament per USB |
| `src/audio_interface/` | Respostes d'àudio del robot |
| `docs/` | Instruccions de muntatge pas a pas (en català) |
| `analysis/` | Scripts de l'article: prova del reconeixement d'ordres, simulació del programa del VEX i proves de veu |

## 🧩 Què cal

- Un kit **VEX IQ (2a generació)** amb el Brain, el comandament i tres Smart Motors (safata al port 4, braç al port 1, xeringa al port 3). Les peces i el muntatge són a `docs/`.
- Un **ordinador** amb micròfon i Python 3.9 o superior.

## ▶️ Com fer-lo funcionar

1. Carregueu `src/main.py` al VEX IQ Brain amb VEXcode IQ.
2. Connecteu el Brain a l'ordinador per USB.
3. A l'ordinador, instal·leu les dependències i engegueu el control per veu:
   ```bash
   pip install -r requirements.txt
   python src/control_veu.py
   ```
   El programa detecta el port del robot automàticament. La primera vegada descarrega el model de Whisper.

## 🗣️ Ordres de veu

| Ordre | Exemples | Què fa |
|---|---|---|
| Esquerra / Dreta | «esquerra», «dreta» | Mou la safata un pas (150°), fins a tres passos a cada costat |
| Puja / Baixa | «puja», «baixa» | Puja o baixa el braç fins a una altra ordre |
| Xucla | «xucla» | Omple la xeringa fins al límit |
| Buida | «buida» | Buida la xeringa |
| Atura't | «atura't», «para», «stop» | Ho atura tot |

El comandament de VEX té sempre prioritat sobre la veu, i la fletxa avall de la creueta ho atura tot.

## 📌 Versions

- **`v1.0-juny2026`**: el codi tal com es va fer servir al taller del 20 de juny de 2026 i tal com s'analitza a l'article.
- Les versions posteriors inclouen les correccions descrites a l'article (reconeixement d'ordres per paraules senceres, límits del braç i control manual momentani).

## 📜 Llicència

- Codi (`src/`, `analysis/`): **MIT**
- Documentació (`docs/`): **CC BY 4.0**

## 👥 Autoria i finançament

- **Investigadors principals:** Marta Tarrés i Toni Dorado, Grup de Recerca RISS, Universitat Politècnica de Catalunya (UPC).
- **Desenvolupament tècnic:** Xènia Mata Fernández.
- **Finançament:** Departament d'Igualtat i Feminismes de la Generalitat de Catalunya (IFE038/24/000087).

Si feu servir o adapteu aquest material, ens agradarà saber-ho: escriviu a quibot@upc.edu o obriu una *issue*.

## ⚠️ Avís legal i seguretat

- **Exempció de responsabilitat:** aquest repositori es proporciona «tal com és» (*AS IS*), amb finalitats exclusivament docents i de recerca. Els autors i la UPC no assumeixen cap responsabilitat pels danys derivats del muntatge o de l'ús del robot.
- **Seguretat:** el robot té parts mòbils. Feu-lo servir sempre amb la supervisió d'una persona adulta, i tingueu a mà el comandament per aturar-lo.
- **Suport:** el projecte es manté en el marc de les activitats de recerca del grup RISS, sense compromís d'assistència tècnica a tercers.
