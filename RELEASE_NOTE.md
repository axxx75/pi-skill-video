# Release notes — pi-skill-video

Formato: una sezione per versione, dalla più recente. Ogni voce = modifica testata e accettata da Axxx,
allineata su tre punti (repo locale `~/PI/repos/pi-skill-video`, checkout installato, GitHub).
Le versioni precedenti sono ricostruibili dalla storia git.

## 1.0.0 — 2026-11-09

**Prima release: pipeline video demo, adattata all'ecosistema WSL no-sudo.**

Fonti: `/brag` (latent-spaces, MIT) per la disciplina dell'output e dei dati demo; HyperFrames
(heygen, Apache-2.0) come motore; la guida interna del video Vault Hub per le regole di qualità.
Dettaglio delle deviazioni in `docs/riferimenti.md`.

- `skills/video/scripts/shoot.mjs` — screenshot 1920×1080 con `playwright-core` e Chrome headless
  gia' presente; scoperta del binario in cache, `CHROME_BIN` come override; `about:blank` prima di
  ogni scena (la navigazione solo-hash non ricarica e produceva scene identiche); supporto
  `click`/`fill`/`press`/`wait` per gli stati con interazione.
- `skills/video/scripts/compose.py` — audio per scena con `edge-tts` (idempotente, `--force-tts`),
  durate misurate con `ffprobe`, una **sub-composizione** per scena (`video/scenes/<id>.html`) e un
  `video/index.html` con host in timeline e audio a tempo assoluto. Deriva lenta, zoom sul punto,
  titolo 40 px, cerchio di evidenza dentro il contenitore scalato (fuori, restava indietro).
  `lead: 0` di default → il primo fotogramma e' il poster (`first_frame_empty` evitato).
- `skills/video/scripts/render.sh` — `check` + `render` + normalizzazione `loudnorm` a -16 LUFS
  (il primo prototipo usciva a -17.5), con misura prima/dopo.
- `skills/video/tests/selftest.sh` — collaudo end-to-end **offline**: pagina demo, audio sintetico,
  render, verifica che l'mp4 abbia traccia audio e durata attesa.
- Voce: `edge-tts` (Isabella) come default italiano, Kokoro offline (`if_sara`, `im_nicola`) come
  alternativa via `HYPERFRAMES_PYTHON`.
- `docs/riferimenti.md` — fonti, licenze, deviazioni motivate, stato dell'ambiente.

Toolchain installata fuori dal pacchetto (in `~/.local`, riproducibile con
`~/PI/scripts/video/install.sh`): FFmpeg 7.0.2 static, shim `unzip`, venv `edge-tts` e `kokoro`,
`chrome-headless-shell` 157. `doctor` verde (whisper/BGM opzionali esclusi). `selftest.sh` OK.
