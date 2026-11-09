# Riferimenti — da dove viene la skill `video` e cosa abbiamo cambiato

Data: 2026-11-09. Pipeline costruita per i video demo delle app interne (prima: "Vault Hub",
guida scritta a mano su Windows). Questo file è il registro delle fonti e delle deviazioni:
se una scelta sembra strana, la motivazione è qui.

## Fonti di partenza

| Fonte | Licenza | Cosa abbiamo preso |
|---|---|---|
| <https://github.com/latent-spaces/brag> (`/brag`) | MIT | l'idea di un output `brag-output/` non versionato, la disciplina "dati demo, mai reali", la checklist di consegna. **Non** il flusso: brag legge il codice del sito e produce un video di lancio di 15-25 s senza screenshot reali — un altro prodotto. |
| <https://github.com/heygen-com/hyperframes> (`hyperframes` 0.9.26) | Apache-2.0 | il motore: HTML+GSAP → MP4, `check`, `render`, sub-composizioni, attributi di timing, lint. Le 4 skill core (`hyperframes`, `hyperframes-cli`, `hyperframes-registry`, `media-use`) si installano da sole in `~/.agents/skills/` con `npx hyperframes init`: **non le duplichiamo qui**. |
| Guida "video lungo (3 min) di un'app, con voce naturale" (Axxx, per il video Vault Hub) | interna | la struttura in 4 fasi (demo → screenshot → voce per scena → composizione+encode), le regole di qualità (deriva, zoom, primo frame, 28 px, -16 LUFS, ascolto completo) e la tabella degli errori già pagati. |
| `edge-tts` (Microsoft Edge TTS) | GPL-3.0 (CLI) | la voce italiana neurale, una chiamata per scena. |
| `kokoro-onnx` via HyperFrames (`hyperframes tts`) | Apache-2.0 | la voce offline di riserva, per testi che non devono uscire dalla macchina. |

## Cosa abbiamo cambiato, e perché

| Deviazione | Perché |
|---|---|
| **Nessun Chrome di Windows.** Playwright e HyperFrames usano `chrome-headless-shell` Linux in `~/.cache/puppeteer`. | WSL: l'exe su `/mnt/c` è lento e il CDP attraversa il confine VM. La guida Windows diceva "usa il Chrome installato" perché lì il download falliva per permessi; qui il browser Linux esiste già (puppeteer di `mermaid-cli`) e si installa senza sudo. |
| **FFmpeg static in `~/.local`** (7.0.2, johnvansickle) invece di `apt install`. | WSL no-sudo. 7.0.2 è l'ultima build statica ufficiale: `doctor` avvisa che i valori assoluti di `loudnorm` non sono confrontabili con quelli misurati su 8.0.1 — i target (-16 LUFS) restano validi perché misuriamo e normalizziamo con lo stesso binario. |
| **`unzip` come shim Python in `~/.local/bin`.** | Info-ZIP non c'è e senza sudo non si installa; `hyperframes` e `@puppeteer/browsers` lo invocano per estrarre Chrome. Lo shim copre `-q -o -d -l` e ripristina il bit eseguibile (senza quello Chrome non parte). |
| **`edge-tts` come voce di default, Kokoro come alternativa offline.** | La guida aveva Kokoro via HyperFrames; in italiano `edge-tts` (Isabella) è più naturale e non scarica 311 MB di modello. Kokoro resta installato perché l'utente vuole provare entrambi e perché è l'unica voce senza traffico verso l'esterno. |
| **Scene generate da script (`compose.py`) e non scritte a mano.** | La guida lo chiedeva già ("cambiare una frase non deve voler dire rifare tutto"). In più `check` pretende una sub-composizione per scena: generarle è l'unico modo per non duplicare errori. |
| **`lead: 0` e titolo al primo fotogramma.** | `first_frame_empty` è un warning di `check` e il primo frame è il poster nei player social. La guida diceva "titolo visibile dal primo fotogramma": ora è imposto dalla configurazione, non dalla disciplina di chi scrive. |
| **Cerchio di evidenziazione dentro il contenitore zoomato.** | Trovato nel primo collaudo: SVG fuori da `.wrap` → il cerchio non seguiva lo zoom e finiva sul titolo invece che sulla card. Le coordinate ora sono sempre quelle dello screenshot. |
| **`render.sh` normalizza a -16 LUFS con `loudnorm`.** | La guida lo faceva a mano alla fine. Un passaggio scriptato evita di consegnare video a -17.5 LUFS (misurato sul primo prototipo). |
| **`playwright-core` + `require` (non `import`).** | `require` rispetta `NODE_PATH`: le dipendenze Node stanno nel progetto video (`npm i playwright-core`), non dentro il pacchetto della skill installato in `~/.pi/agent/git/...`. |

## Cosa **non** abbiamo preso

- **`/brag-slim`**: è un flusso per Opus 5.5 che scrive il video da zero, senza HyperFrames. Noi vogliamo il motore deterministico.
- **letsbrag.app / HeyGen cloud / HyperFrames Pro**: servizi esterni a pagamento. Vietati dall'isolamento esterno.
- **whisper-cpp (trascrizione/sottotitoli)**: opzionale, non installato. Se servono i sottotitoli, `edge-tts --write-subtitles` basta per il parlato che generiamo noi.
- **MusicGen (musica generata)**: pesante (torch) e non necessario. La musica si prende da tracce CC0/CC BY (`media-use` ha i riferimenti).
- **Kokoro come default**: vedi sopra.

## Stato dell'ambiente (2026-11-09)

```
ffmpeg/ffprobe   7.0.2-static        ~/.local/bin (→ ~/.local/opt/ffmpeg-7.0.2)
unzip            shim 1.0            ~/.local/bin/unzip
edge-tts         7.3.1               ~/.local/bin (→ venv ~/.local/opt/edge-tts)
kokoro-onnx      ultima               ~/.local/opt/kokoro (HYPERFRAMES_PYTHON)
chrome-headless-shell 157            ~/.cache/puppeteer/... (HYPERFRAMES_BROWSER_PATH)
hyperframes CLI  0.9.26              npx (nessuna install globale)
```

Verifica: `npx -y hyperframes@0.9.26 doctor` (whisper/BGM restano ✗: sono opzionali).
Collaudo della pipeline: `bash skills/video/tests/selftest.sh` → `OK`.
