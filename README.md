# pi-skill-video

Skill per [pi](https://pi.dev) che gira **video demo di un'app web** con voce narrante italiana:
screenshot reali (Playwright), voce per scena (edge-tts o Kokoro offline), composizione e render
(HyperFrames), encode e loudness (FFmpeg).

Il video si adatta alla voce: ogni scena dura quanto la sua frase più un respiro. Una funzione =
una scena = uno screenshot reale, con deriva lenta, zoom sul punto descritto e cerchio di
evidenza sincronizzato.

## Installazione

```bash
pi install git:github.com/axxx75/pi-skill-video
```

Dipendenze della toolchain (no-sudo, tutto in `~/.local`):

```bash
bash ~/PI/scripts/video/install.sh
npx -y hyperframes@0.9.26 doctor     # whisper/BGM sono opzionali
```

Il dettaglio delle fonti e delle deviazioni rispetto alla guida originale sta in
[`docs/riferimenti.md`](docs/riferimenti.md).

## Uso

Nella cartella di lavoro del video (quella con `scenes.json`):

```bash
npm i playwright-core                                  # una volta per progetto
node  <skill>/scripts/shoot.mjs  scenes.json           # screenshot reali
python3 <skill>/scripts/compose.py scenes.json         # voce + timeline + HTML
bash  <skill>/scripts/render.sh                        # check + render + -16 LUFS
```

`scenes.json` dichiara le scene: url, eventuali interazioni, la frase di voce, il titolo, il punto
dello zoom e il cerchio di evidenza. Schema completo e regole di qualità in
[`skills/video/SKILL.md`](skills/video/SKILL.md).

## Collaudo

```bash
bash skills/video/tests/selftest.sh    # offline: pagina demo, audio sintetico, render, verifica mp4
```

## Requirements

| Componente | Versione / note | Obbligatorio |
|---|---|---|
| Node.js | ≥ 22 (HyperFrames) | sì |
| Python 3 | ≥ 3.10 (script + edge-tts) | sì |
| FFmpeg / ffprobe | static 7.0.2 in `~/.local/bin` | sì |
| Chrome headless | `chrome-headless-shell` in `~/.cache/puppeteer` | sì |
| `unzip` | shim Python in `~/.local/bin` (serve a HyperFrames) | sì |
| `edge-tts` | venv in `~/.local/opt/edge-tts` | sì per la voce online |
| `playwright-core` | nel progetto video (`npm i playwright-core`) | sì |
| `kokoro-onnx` + `soundfile` | venv `~/.local/opt/kokoro`, `HYPERFRAMES_PYTHON` | no (voce offline) |
| HyperFrames CLI | `npx hyperframes@0.9.26` (nessuna install globale) | sì |

## Privacy

`edge-tts` invia il testo ai server Microsoft: solo frasi di demo, mai dati reali di persone o
clienti. Per i testi che non devono uscire usare Kokoro offline. I video si fanno su **dati demo**
e su un **server demo**: nessun URL interno, nessuna email, nessun token in vista.

## Licenza

MIT — vedi [`LICENSE`](LICENSE).
