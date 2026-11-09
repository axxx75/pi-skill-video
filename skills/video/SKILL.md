---
name: video
description: Gira una demo video di un'app web (o di qualsiasi cosa visibile in un browser) con voce narrante italiana, con screenshot reali con Playwright, voce neurale con edge-tts (o Kokoro offline), composizione e render con HyperFrames, encode e loudness con FFmpeg. Usa quando l'utente chiede un video demo, un walkthrough, un video di 1-3 minuti di un prodotto, o dice "fai il video di questa app".
---

# video

Una funzione = una scena. Ogni scena: **screenshot reale** + **una frase di voce** + zoom sul punto descritto.
Il video si adatta alla voce (durata = audio + respiro), mai il contrario.

## Pipeline

```
scenes.json ──shoot.mjs──▶ video/assets/<id>.png     (Playwright + Chrome headless)
            ──compose.py─▶ video/assets/<id>.mp3     (edge-tts, una chiamata per scena)
                        ─▶ video/scenes/<id>.html    (sub-composizione: zoom, titolo, cerchio)
                        ─▶ video/index.html          (host in timeline + audio assoluto)
            ──render.sh──▶ video/renders/final.mp4   (check + render + loudnorm)
```

Comandi, dalla cartella di lavoro del video (quella con `scenes.json`):

```bash
# percorso del pacchetto installato (o del sorgente, durante lo sviluppo)
SKILL="${PI_SKILL_VIDEO_DIR:-$HOME/.pi/agent/git/github.com/axxx75/pi-skill-video/skills/video}"
export NODE_PATH="$PWD/node_modules"                     # serve a shoot.mjs (vedi Setup)

node    "$SKILL/scripts/shoot.mjs" --probe <url|pagina>  # esplorazione: screenshot + coordinate
node    "$SKILL/scripts/shoot.mjs" scenes.json           # screenshot delle scene
python3 "$SKILL/scripts/compose.py" scenes.json          # --force-tts per rigenerare la voce
python3 "$SKILL/scripts/compose.py" scenes.json --subs   # + video/renders/subtitles.vtt
bash    "$SKILL/scripts/render.sh"                       # check + render + -16 LUFS
```

Idempotente: l'audio si rigenera solo se il file manca; lo screenshot si rifà sempre; `compose.py` riscrive l'HTML e stampa il piano (start, durata audio, totale).

## Setup (una volta, no-sudo)

| Strumento | Verifica |
|---|---|
| FFmpeg/ffprobe static in `~/.local/bin` | `ffmpeg -version` |
| `edge-tts` in venv + symlink in `~/.local/bin` | `edge-tts --version` |
| Kokoro offline: `HYPERFRAMES_PYTHON` → venv con `kokoro-onnx soundfile` | `echo $HYPERFRAMES_PYTHON` |
| Chrome headless | `ls ~/.cache/puppeteer/chrome-headless-shell/*/` |
| `playwright-core` nel progetto video | `npm i playwright-core` + `export NODE_PATH=$PWD/node_modules` |
| HyperFrames | `npx -y hyperframes@0.9.26 doctor` → tutto ✓ (whisper/BGM opzionali) |

Install completo dell'ecosistema: `bash ~/PI/scripts/video/install.sh` (idempotente, no sudo).

## Prima di scrivere le scene (esplorazione)

Due passi, in quest'ordine. Saltarli costa render buttati.

```bash
node "$SKILL/scripts/shoot.mjs" --probe http://127.0.0.1:8000/index.html \
     http://127.0.0.1:8000/volumi.html http://127.0.0.1:8000/analytics.html
```

- Un PNG per pagina in `video/probe/` (niente voce, niente composizione) e, per ogni pagina,
  le coordinate dei blocchi che di solito si evidenziano: `h1`, `h2`, ogni figlio di `#kpi` e di
  `#filters`, con `cx`/`cy` in pixel dello screenshot.
- **`zoom` e `highlight` si prendono da quelle coordinate**, non a occhio sulla foto: un cerchio
  sbagliato di 200 px si vede subito nel video e non nel PNG.
- Per gli elementi fuori da quei contenitori: `page.evaluate` con `getBoundingClientRect()` in uno
  script usa-e-getta, oppure si aggiunge il selettore a quelli del probe.
- Il probe serve anche a scoprire quali pagine chiedono al server cose lente o laterali
  (`/api/perf`, `/api/box`): nella scena quelle rotte si disattivano (`?perf=0`) o si evitano.

Solo dopo si scrive `scenes.json`: una funzione = una scena, e ogni scena ha il suo screenshot reale.

## Video da 3 minuti

| Grandezza | Valore |
|---|---|
| Parlato con `rate -5%` | ~150 parole/minuto |
| 3 minuti | 400-450 parole totali |
| Scene | 12-15 da 10-20 s (una funzione = una scena) |
| Durata scena | audio + 0,5-1 s di respiro (`pause`) |

Ordine che regge: promessa (15 s) → dashboard → integrazioni → funzioni distintive →
sicurezza/ruoli → chiusura con il payoff. Oltre i 3 minuti serve un motivo: il taglio è la prima
leva, non l'aggiunta.

## Sottotitoli

`compose.py --subs` scrive `video/renders/subtitles.vtt` per il video intero: i cue arrivano da
`edge-tts --write-subtitles` (tempi parola per parola) e vengono spostati sull'inizio di ogni scena.
Se un mp3 esiste già senza `.vtt`, quel giro richiama edge-tts (`--subs --force-tts` rigenera tutto).
Da caricare come sidecar su YouTube/LinkedIn; per averli dentro l'mp4:

```bash
ffmpeg -i video/renders/final.mp4 -i video/renders/subtitles.vtt -c copy -c:s mov_text out.mp4
```

## scenes.json

```json
{
  "title": "Titolo del video",
  "voice": "it-IT-IsabellaNeural",
  "rate": "-5%",
  "lead": 0.0,
  "pause": 0.7,
  "tail": 1.2,
  "scenes": [
    {
      "id": "s1",
      "url": "http://127.0.0.1:8000/app#dashboard",
      "steps": [{ "click": "#tab-cost" }, { "fill": ["#user", "demo"] }, { "wait": 250 }],
      "voice": "Una frase breve, come si parla. Massimo venti parole.",
      "title": "Etichetta in basso (40 px)",
      "zoom": { "cx": 480, "cy": 300, "scale": 1.14 },
      "highlight": { "x": 232, "y": 322, "r": 118 }
    }
  ]
}
```

- `url`: URL http (server demo) o percorso locale. Il `#hash` è supportato.
- `steps`: `click`, `fill` (`[selettore, valore]`), `press`, `wait` (ms). Servono per gli stati con interazione (login digitato, pannello aperto).
- `zoom.cx/cy`: centro dello zoom **in pixel dello screenshot** (1920×1080). `scale` 1.03-1.2; oltre 1.25 il testo si sfoca.
- `highlight.x/y/r`: cerchio in pixel dello screenshot, sincronizzato con la frase (appare a 0.6 s, sparisce a 3.2 s).
- `lead` **0**: il primo fotogramma deve già mostrare immagine e titolo (è il poster nei player social).
- `pause`: respiro fra le scene. `tail`: coda finale.

## Voce

Due motori, entrambi installati:

```bash
# 1. edge-tts — online, la migliore italiana. Il testo va ai server Microsoft: mai dati reali.
edge-tts --list-voices | grep it-IT
#   it-IT-IsabellaNeural (consigliata) · it-IT-ElsaNeural · it-IT-DiegoNeural · it-IT-GiuseppeMultilingualNeural

# 2. Kokoro (82M, offline, via HyperFrames) — per testi che non devono uscire
export HYPERFRAMES_PYTHON=$HOME/.local/opt/kokoro/bin/python
npx -y hyperframes@0.9.26 tts "testo" --voice if_sara --lang it --output out.wav
#   voci italiane: if_sara, im_nicola (prefisso i = italiano)
```

Regole: `rate` fra -5% e -8% (oltre -10% suona lento), frasi ≤ 20 parole, una idea per frase, sigle scritte come si leggono, numeri in lettere se escono male. Ascoltare **tutto** prima di consegnare: è l'unico controllo che i frame non fanno.

Per usare Kokoro al posto di edge-tts: generare i file `video/assets/<id>.mp3` con `hyperframes tts` (o convertire i wav) e lanciare `compose.py` senza `--force-tts`, che misura le durate già presenti.

## Musica e livelli

- Musica **sotto** la voce: -22/-26 dB rispetto al parlato, dissolvenza finale 2-3 s.
- Brano CC BY (Sascha Ende) → citarlo nel testo di condivisione. CC0 / YouTube Audio Library → nessun obbligo.
- Bilanciare misurando: `render.sh` porta il mix a **-16 LUFS**, TP -1.5. Se la voce è coperta, abbassare la musica — mai alzare la voce.
- Aggiungere un `<audio>` musicale in `video/index.html` con `data-start="0"`, `data-volume` basso, e ritoccare `data-fade-out`.

## Regole di contenuto

- **Solo dati demo.** Server demo con dati inventati; mai l'app interna vera, mai email, hostname o token in vista. Dichiarare "dati di esempio" a schermo.
- Se l'app ha SSO, il server demo salta l'autenticazione (sessione finta).
- Se una funzione è nel video, deve avere il suo screenshot reale: niente slide inventate.
- Niente schermata ferma oltre 5 s: ogni scena ha deriva lenta (lo zoom è già nel template) e un punto evidenziato.
- Testi sotto i 28 px su 1080p non si leggono: usare lo zoom o allargare i dati demo.
- Output (`video/`, `brag-output/`, mp3, png, render) **non** va committato: è materiale di lavoro.

## Errori noti

| Sintomo | Causa | Rimedio |
|---|---|---|
| `Check failed: No composition found` | `compose.py` lanciato in una cartella senza `scenes.json` | cd nella cartella di lavoro del video |
| Tutte le scene con lo stesso screenshot | navigazione solo-hash che non ricarica | già gestito (`about:blank` prima di ogni scena) |
| `nested_structure_needs_subcomposition` | scene scritte a mano dentro l'index | usare `compose.py`: una sub-composizione per scena |
| `first_frame_empty` | `lead` > 0 o titolo che entra dopo | `lead: 0`, titolo visibile a 0 s |
| Cerchio disallineato dopo lo zoom | SVG fuori dal contenitore scalato | l'SVG sta dentro `.wrap` (già così) |
| Voce robotica | voce SAPI/Windows o TTS di sistema | edge-tts neurale |
| `MODULE_NOT_FOUND: playwright-core` | `shoot.mjs` risolve dal proprio path, non dalla cwd | `export NODE_PATH=<progetto>/node_modules` |
| Cerchio o zoom sul punto sbagliato | coordinate stimate a occhio sulla foto | `--probe` e copiare `cx`/`cy` dai blocchi veri |
| Scena statica che annoia | nessuna deriva, nessuno zoom | `zoom.scale` 1.05-1.2 sempre, più un `highlight` |
| Render lentissimo | capture via screenshot | `HYPERFRAMES_BROWSER_PATH` → chrome-headless-shell (2.6× più veloce) |
| Mezzo schermo vuoto | screenshot piccolo su canvas geometrico | zoom sul riquadro o più dati demo |

## Riferimenti

- `docs/riferimenti.md` in questo pacchetto: da dove viene la pipeline, cosa abbiamo cambiato e perché.
- Skill HyperFrames installate in `~/.agents/skills/`: `hyperframes` (contratto di render), `hyperframes-cli`, `hyperframes-registry` (~450 blocchi pronti), `media-use` (musica, SFX, voiceover).
- Video brevi di lancio (20 s, musica+SFX+copy): skill `brag` in `~/.agents/skills/brag`.
