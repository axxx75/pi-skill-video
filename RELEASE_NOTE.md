# Release notes — pi-skill-video

## 1.0.4 — 2026-11-09

- `shoot.mjs --probe`: il nome dei PNG non si porta dietro la query (`02-volumi.html_perf_0.png`
  → `02-volumi.png`). Il `?perf=0` resta nell'URL, non nel nome del file.

Test: `selftest.sh` OK.

## 1.0.3 — 2026-11-09

**Le lacune emerse dalla guida del video lungo (Vault Hub), chiuse dove costavano di più.**

- `shoot.mjs --probe <url|pagina> [...]` — esplorazione prima di scrivere le scene: un PNG per
  pagina in `video/probe/` e, per ogni pagina, `cx`/`cy` dei blocchi che si evidenziano (`h1`,
  `h2`, figli di `#kpi` e di `#filters`). Nasce da un errore pagato: coordinate stimate a occhio =
  tre render con il cerchio sul riquadro sbagliato.
- `compose.py --subs` — `video/renders/subtitles.vtt` per il video intero, dagli
  `--write-subtitles` di edge-tts (tempi veri, non spalmati a mano) spostati sull'inizio di ogni
  scena. Se un mp3 c'è ma il `.vtt` no, quel giro richiama edge-tts da solo.
- `SKILL.md`: sezioni **Prima di scrivere le scene** (probe, coordinate, rotte da disattivare tipo
  `?perf=0`) e **Video da 3 minuti** (150 parole/min, 400-450 parole, 12-15 scene da 10-20 s),
  sezione **Sottotitoli**, `NODE_PATH` nei comandi e nel Setup, tre righe nuove nella tabella
  degli errori noti.
- `selftest.sh`: copre `--probe` (PNG + coordinate).

Test: `selftest.sh` OK (6,0 s). `--subs` provato sul video demo di pure-obs: 6 cue, tempi
allineati alle scene (0.1 s, 3.75 s, … 30.53 s).

## 1.0.2 — 2026-11-09

**Skill non caricabile: frontmatter YAML malformato.**

- `skills/video/SKILL.md`: `description:` conteneva `italiana: screenshot reali`. In YAML un
  `: ` dentro un valore non quotato apre una mappatura annidata → pi segnalava
  `Nested mappings are not allowed in compact mappings at line 2, column 14` e scartava la skill.
  Ora `italiana, con screenshot reali` (testo invariato nella sostanza, virgola al posto dei due punti).

Verifica: frontmatter parsa con `yaml.safe_load` (chiavi `name`, `description`); `selftest.sh` OK.
Controllate tutte le skill installate: nessun altro `description` non quotato con `: `.

## 1.0.1 — 2026-11-09

**Due difetti trovati uscendo dal prototipo (dove script e progetto stavano nella stessa cartella).**

- `render.sh` faceva `cd ../../..` assumendo di stare dentro il progetto video: dal checkout
  installato finiva nella radice del pacchetto (`No composition found`). Ora si esegue **dalla
  cartella del video**, entra in `video/` per `check`/`render` (HyperFrames legge la cwd) e scrive
  `final.mp4` in `video/renders/`.
- `SKILL.md` indicava come default il repo sorgente; ora punta al **checkout installato**
  (`~/.pi/agent/git/github.com/axxx75/pi-skill-video/skills/video`), con `PI_SKILL_VIDEO_DIR` come
  override per lo sviluppo.
- `selftest.sh` ora esegue `render.sh` (prima replicava i comandi a mano: per questo il `cd`
  sbagliato era invisibile) e verifica `final.mp4`.

Test: `selftest.sh` OK (5.8 s, audio aac, loudnorm misurato prima/dopo). Collaudo reale su un video
di 3 scene: 21.3 s, -17.5 → -16.4 LUFS.

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
