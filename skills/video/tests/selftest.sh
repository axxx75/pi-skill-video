#!/usr/bin/env bash
# selftest.sh — collaudo end-to-end offline della pipeline video (niente rete TTS).
# Genera una pagina demo, 2 scene, audio sintetico, screenshot reali, render e verifica l'mp4.
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

for tool in node python3 ffmpeg ffprobe npx; do
  command -v "$tool" >/dev/null || { echo "MANCA $tool"; exit 2; }
done

echo "== 1/5 pagina demo + scenes.json =="
mkdir -p demo video/assets
cat > demo/app.html <<'HTML'
<!doctype html><meta charset="utf-8">
<style>
 body{margin:0;width:1920px;height:1080px;background:#0f1117;color:#e8eaf0;font:24px system-ui}
 h1{font-size:64px;margin:80px 64px 24px} .box{display:flex;gap:32px;padding:0 64px}
 .card{background:#161a24;border:1px solid #232838;border-radius:16px;padding:32px;width:400px}
 .card b{display:block;font-size:52px;margin-top:12px}
 .hidden{display:none}
</style>
<h1 id="t">Demo</h1>
<div class="box">
  <div class="card">Utenti<b>186</b></div>
  <div class="card">Array<b>43</b></div>
  <div class="card">Volumi<b>8374</b></div>
</div>
<script>
 const [v] = [location.hash || '#a'];
 document.querySelector('h1').textContent = v === '#b' ? 'Seconda vista' : 'Prima vista';
</script>
HTML

cat > scenes.json <<'JSON'
{
  "title": "selftest",
  "voice": "it-IT-IsabellaNeural",
  "lead": 0.0,
  "pause": 0.4,
  "tail": 0.6,
  "scenes": [
    { "id": "s1", "url": "demo/app.html#a", "voice": "scena uno",
      "title": "Prima scena", "zoom": { "cx": 700, "cy": 400, "scale": 1.15 },
      "highlight": { "x": 400, "y": 330, "r": 110 } },
    { "id": "s2", "url": "demo/app.html#b", "voice": "scena due",
      "title": "Seconda scena", "zoom": { "cx": 960, "cy": 540, "scale": 1.05 } }
  ]
}
JSON

echo "== 2/5 audio sintetico (offline) =="
for id in s1 s2; do
  ffmpeg -hide_banner -v error -y -f lavfi -i anullsrc=r=48000:cl=mono -t 2 -q:a 9 "video/assets/$id.mp3"
done
ls -l video/assets

echo "== 3/5 playwright-core + probe =="
if [ ! -d "$SKILL/scripts/node_modules/playwright-core" ] && [ ! -d node_modules/playwright-core ]; then
  npm i --silent --no-save playwright-core >/dev/null 2>&1 || { echo "playwright-core non installabile"; exit 2; }
fi
export NODE_PATH="$(pwd)/node_modules:$SKILL/scripts/node_modules"
node "$SKILL/scripts/shoot.mjs" scenes.json
# --probe: esplorazione prima delle scene. Deve scrivere il PNG e le coordinate dei blocchi.
node "$SKILL/scripts/shoot.mjs" --probe "demo/app.html#b" | tee probe.log
[ -s "$(ls video/probe/*.png 2>/dev/null | head -1)" ] || { echo "FAIL: probe senza screenshot"; exit 1; }
grep -q 'cx=' probe.log || { echo "FAIL: probe senza coordinate"; exit 1; }

echo "== 4/5 compose + render =="
cp "$SKILL/templates/hyperframes.json" video/
python3 "$SKILL/scripts/compose.py" scenes.json
bash "$SKILL/scripts/render.sh" 2>&1 | tail -8

echo "== 5/5 verifica =="
MP4="video/renders/final.mp4"
[ -s "$MP4" ] || MP4="$(ls -t video/renders/*.mp4 | head -1)"
[ -s "$MP4" ] || { echo "FAIL: nessun mp4"; exit 1; }
AUDIO="$(ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$MP4")"
DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MP4")"
[ -n "$AUDIO" ] || { echo "FAIL: mp4 senza audio"; exit 1; }
python3 - "$DUR" <<'PY'
import sys
d = float(sys.argv[1])
assert d > 4.5, f"FAIL: durata {d:.2f}s troppo corta"
print(f"durata {d:.2f}s")
PY
echo "OK  $MP4  (audio: $AUDIO)"
