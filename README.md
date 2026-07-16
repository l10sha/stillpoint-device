# StillPoint — Virtual Device

A software twin of the StillPoint hardware described in `stillpoint-prd.docx`:
the 7.5″ e-ink panel, the Pi 5 + Hailo application layer, the daily rhythm
engine, guided sessions, micro-practice invitations, and email triage — all
running locally, visualized in a browser as the physical device.

## Run

```bash
cd virtual-device
python3 run.py                # optional: --time 07:30  --port 8777
# open http://127.0.0.1:8777
```

Requires Python 3.10+ with Pillow (`pip install pillow`). Nothing else.
No network access, no cloud — in the spirit of the product.

## What's real vs. simulated

| PRD component | In the virtual device |
|---|---|
| E-ink panel (7.8″ Carta 1300, 1404×1072, 16-gray) | `firmware/panel.py` — same driver API as a real EPD (init/display/display_partial/sleep), quantizes to 16 levels; the shell renders full-refresh inversion flashes and partial-refresh ghosting on the 3D device |
| Display Manager / typography | `firmware/renderer.py` — PIL composition, Georgia serif, PRD layout rules (≤3 elements, high whitespace) |
| Scheduler + Daily Rhythm Engine | `firmware/device.py` — phase table from PRD §5.5, ambient rotation, invitations with 60s no-guilt timeout |
| Local LLM (Qwen 2.5 1.5B on Hailo) | `firmware/llm.py` — deterministic stub behind the real interface; simulates accelerator latency/token rate. Swap the method bodies for llama.cpp/Ollama calls |
| TTS (Chatterbox / Piper) | Browser `speechSynthesis` (a real local TTS), paced at meditation speed; chime is a WebAudio struck-bowl synth |
| Email Bridge (IMAP + classify) | `firmware/device.py` + `llm.py` — header-only classification into ignore / review-later / act-now; act-now surfaces a calm one-liner, everything else is held silently |
| Enclosure, walnut haptic lid | `shell/` — CSS/canvas device; clicking the lid is the capacitive tap |
| SimClock | `firmware/simclock.py` — warp/accelerate time to demo the whole day |

## Porting to real hardware

The application layer only touches `VirtualEPD`, the event bus, and `SimClock`.
On a real Pi: replace `panel.py` with the Waveshare SPI driver, route `speak`/
`chime` events to the I2S DAC pipeline (Piper first, Chatterbox later), replace
`llm.py` stubs with llama.cpp on the Hailo, and read GPIO/cap-touch instead of
POST `/input`. `device.py`, `renderer.py`, and `content.py` run unchanged.
