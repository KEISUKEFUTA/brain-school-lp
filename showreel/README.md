# 二川佳祐 Showreel 2026 (15s)

- `futakawa_showreel.mp4` — 完成版（1920×1080 / 30fps / 15秒 / 音声つき）
- `index.html` — 動画のもとになるアニメーション本体。ブラウザで開いて ▶ を押すと音つきでリアルタイム再生
- `soundtrack.py` — BGM・効果音をコードで合成（120BPM。場面の切り替わりが全部ビートに合う）
- `render.cjs` — Playwright で1フレームずつ書き出し、ffmpeg で動画にまとめる
- `fetch_fonts.py` — 使用フォント（M PLUS 1 / Poppins）をダウンロードして `fonts/` に保存

## 再生成
```
python3 soundtrack.py
PW=<playwright path> FFMPEG=<ffmpeg path> node render.cjs video.mp4
ffmpeg -i video.mp4 -i soundtrack.wav -c:v libx264 -crf 21 -pix_fmt yuv420p -c:a aac -shortest futakawa_showreel.mp4
```
