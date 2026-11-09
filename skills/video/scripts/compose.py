#!/usr/bin/env python3
"""compose.py — da scenes.json a progetto Hyperframes + audio.

  scenes.json  ->  video/assets/*.png (da shoot.mjs) , video/assets/*.mp3 (edge-tts)
                   video/scenes/<id>.html (una sub-composizione per scena)
                   video/index.html (host in timeline + audio per scena)

Idempotente: l'audio si rigenera solo se manca (--force-tts per rigenerarlo).
Uso: python3 compose.py scenes.json [--force-tts]
"""
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Radice del progetto video = cartella che contiene scenes.json (non la cartella della skill).
ROOT = Path.cwd()
VIDEO = ASSETS = SCENES = Path()
W, H = 1920, 1080


def need(tool, hint):
    if not shutil.which(tool):
        sys.exit(f"{tool} non trovato nel PATH. {hint}")


def tts(cfg, scene, force):
    out = ASSETS / f"{scene['id']}.mp3"
    if out.exists() and not force:
        return out
    need("edge-tts", "Installa: python3 -m venv ~/.local/opt/edge-tts && ~/.local/opt/edge-tts/bin/pip install edge-tts")
    txt = ROOT / "audio" / f"{scene['id']}.txt"
    txt.parent.mkdir(exist_ok=True)
    txt.write_text(scene["voice"] + "\n", encoding="utf-8")
    subprocess.run(
        ["edge-tts", "--voice", cfg.get("voice", "it-IT-IsabellaNeural"),
         "--rate", cfg.get("rate", "-5%"), "--file", str(txt), "--write-media", str(out)],
        check=True)
    return out


def duration(path):
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True)
    return float(res.stdout.strip())


def esc(text):
    return html.escape(text, quote=True)


def scene_file(sid, dur, scene):
    zoom = scene.get("zoom") or {}
    scale = float(zoom.get("scale", 1.045))
    cx = float(zoom.get("cx", W / 2)) / W * 100
    cy = float(zoom.get("cy", H / 2)) / H * 100
    hl, title = scene.get("highlight"), scene.get("title")

    circle = ""
    if hl:
        circle = (f'      <circle id="{sid}-circle" cx="{hl["x"]}" cy="{hl["y"]}" r="{hl["r"]}" '
                  f'fill="none" stroke="#7dd3fc" stroke-width="5" opacity="0"/>')
    caption = ""
    if title:
        caption = (f'      <div class="title"><h2 id="{sid}-title">{esc(title)}</h2></div>')

    tweens = [
        f'    tl.fromTo("#{sid}-img", {{ scale: 1 }}, {{ scale: {scale:.4f}, duration: {dur:.3f}, ease: "none" }}, 0);'
    ]
    if title:
        tweens.append(
            f'    tl.fromTo("#{sid}-title", {{ opacity: 0, y: 18 }}, '
            f'{{ opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }}, 0.15);')
    if hl:
        tweens.append(
            f'    tl.fromTo("#{sid}-circle", {{ opacity: 0, scale: 0.6, transformOrigin: "50% 50%" }}, '
            f'{{ opacity: 0.95, scale: 1, duration: 0.5, ease: "power2.out" }}, 0.6);')
        tweens.append(f'    tl.to("#{sid}-circle", {{ opacity: 0, duration: 0.4 }}, 2.8);')

    return f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; }}
    .wrap {{ position: absolute; inset: 0; overflow: hidden; }}
    .wrap img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
    .title {{ position: absolute; left: 64px; bottom: 64px; max-width: 1280px;
              background: rgba(8, 10, 16, .82); border-left: 6px solid #7dd3fc;
              border-radius: 10px; padding: 20px 28px; }}
    .title h2 {{ color: #f4f6fb; font-size: 40px; font-weight: 700; letter-spacing: -.01em; }}
    svg.hl {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
  </style>
  <div id="{sid}" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
    <div class="wrap" style="transform-origin: {cx:.4f}% {cy:.4f}%" data-layout-allow-overflow>
      <img id="{sid}-img" src="../assets/{sid}.png" alt="">
      <svg class="hl" viewBox="0 0 {W} {H}" aria-hidden="true" data-layout-ignore>
{circle}
      </svg>
    </div>
{caption}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tweens)}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def main():
    global ROOT, VIDEO, ASSETS, SCENES
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cfg_path = Path(args[0] if args else "scenes.json").resolve()
    ROOT = cfg_path.parent
    VIDEO = ROOT / "video"
    ASSETS = VIDEO / "assets"
    SCENES = VIDEO / "scenes"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    force = "--force-tts" in sys.argv
    need("ffprobe", "Installa FFmpeg static in ~/.local (vedi README della skill video).")
    for d in (ASSETS, SCENES):
        d.mkdir(parents=True, exist_ok=True)

    pause = float(cfg.get("pause", 0.7))
    lead = float(cfg.get("lead", 0.0))
    tail = float(cfg.get("tail", 1.2))

    starts, audios, plan, t = [], [], [], lead
    for scene in cfg["scenes"]:
        adur = duration(tts(cfg, scene, force))
        starts.append(t)
        audios.append(adur)
        plan.append((scene["id"], t, adur))
        t += adur + 0.3 + pause
    total = starts[-1] + audios[-1] + 0.3 + tail

    hosts, audio_tags, fades = [], [], []
    for i, scene in enumerate(cfg["scenes"]):
        sid = scene["id"]
        slot = (starts[i + 1] if i + 1 < len(starts) else total) - starts[i]
        hosts.append(
            f'    <div id="{sid}" data-composition-id="{sid}" data-composition-src="scenes/{sid}.html"\n'
            f'         data-start="{starts[i]:.3f}" data-duration="{slot:.3f}" data-track-index="{i}"\n'
            f'         data-width="{W}" data-height="{H}"></div>')
        audio_tags.append(
            f'    <audio id="{sid}-audio" class="clip" data-start="{starts[i]:.3f}"\n'
            f'           data-track-index="{100 + i}" data-volume="1" src="assets/{sid}.mp3"></audio>')
        if i > 0:
            fades.append(f'    tl.fromTo("#{sid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "none" }}, {starts[i]:.3f});')
        (SCENES / f"{sid}.html").write_text(scene_file(sid, slot, scene), encoding="utf-8")

    doc = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>{esc(cfg.get('title', 'video'))}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
  #root {{ width: 100%; height: 100%; font-family: Inter, sans-serif; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="{W}" data-height="{H}">
{chr(10).join(hosts)}
{chr(10).join(audio_tags)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(fades)}
    window.__timelines = window.__timelines || {{}};
    window.__timelines["main"] = tl;
    tl.seek(0);
  </script>
</body>
</html>
"""
    (VIDEO / "index.html").write_text(doc, encoding="utf-8")
    for sid, st, ad in plan:
        print(f"{sid}: start {st:6.2f}s  audio {ad:5.2f}s")
    print(f"totale {total:.2f}s -> {VIDEO / 'index.html'}")


if __name__ == "__main__":
    main()
