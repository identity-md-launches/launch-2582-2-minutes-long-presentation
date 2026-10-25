# NIGHTSHIFT — Ideas don't sleep

**Latest version: [TV news remix — artifacts/video-v2.mp4](artifacts/video-v2.mp4).** See [NEWS-V2.md](NEWS-V2.md) for the new format, media specifications, production details and synthetic-presenter limitations. The remainder of this README describes the original v1 input.

A two-minute project presentation for [NIGHTSHIFT](https://getnightshift.tech), built on [IMD](https://imd.fun).

**Delivered video: [`artifacts/video.mp4`](artifacts/video.mp4)** (`video/mp4`). This is the declared output path. The video is intentionally untracked and is uploaded separately by the delivery system.

## Media specification

| Property | Value |
| --- | --- |
| Duration | 120 seconds / 2:00 |
| Dimensions | 1920 × 1080, landscape, 16:9 |
| Frame rate | 24 fps; 2,880 frames |
| Video | H.264 High, level 4.0, yuv420p |
| Audio | AAC, 48 kHz, stereo, 160 kb/s target |
| Browser delivery | MP4 with `moov` before `mdat` (`+faststart`) |
| Size | Under 64 MiB; exact bytes recorded in `review/verification.json` |
| Accessibility | Burned-in English captions; editable `captions.srt` and `captions.json` |

English narration uses the local Piper LJ Speech voice, trained on public-domain recordings. The electronic score is original, synthesized specifically for this presentation; no stock music or audio loops are used. Music is ducked under speech. The master targets −16 LUFS and −1.5 dBTP; measurements of the delivered AAC stream are in the verification record.

## Presentation

| Time | Subject |
| --- | --- |
| 00:00–00:10 | NIGHTSHIFT: ideas don't sleep |
| 00:10–00:20 | Start with an idea, an audience and limits |
| 00:20–00:30 | The CEO's decide, build, ship and learn cycle |
| 00:30–00:40 | The IMD swarm |
| 00:40–00:50 | Digital products and storefronts |
| 00:50–01:00 | Commerce for people and AI agents |
| 01:00–01:10 | Owner direction, budgets and approvals |
| 01:10–01:20 | Flight recorder and books |
| 01:20–01:30 | The station's five rooms |
| 01:30–01:40 | MCP, Swarm Mind and crews |
| 01:40–01:50 | $SHIFT, NIGHT FROGS, games and risk |
| 01:50–02:00 | Visit getnightshift.tech; built on imd.fun |

`storyboard.json` contains the full scene copy and spoken script. `review/storyboard.jpg` is a visual overview. Original motion graphics use the site's purple night palette, animated diagrams, activity highlights and a twelve-part timeline.

## Sources and limitations

Project facts were taken from the following first-party sources on **25 October 2026**:

- [Homepage](https://getnightshift.tech/), retained as `sources/homepage.html`: identity, station framing and room names.
- [Public project guide](https://getnightshift.tech/llms.txt), retained as `sources/nightshift-llms.txt`: rooms, public MCP, Swarm Mind, crews and ecosystem.
- [Whitepaper](https://getnightshift.tech/whitepaper.md), retained as `sources/whitepaper.md`: company shifts, spending controls, products, x402/USDC on Base, flight recorder and risks.
- [Official station artwork](https://getnightshift.tech/art/megastructure.webp) and [crescent mark](https://getnightshift.tech/brand/nightshift-mark.svg): retained in `assets/`. Artwork and branding remain the rights of their respective owners; inclusion illustrates the requested project and does not transfer those rights.

The presentation explains the project's published design. Its panels, brief, workflow, wallet graphic and activity highlights are **illustrative motion graphics**, not captured sessions, real transaction receipts or measured company results. The example brief is explicitly labeled. Public product availability can change; some project documents may lag newer releases. No product functionality, profitability, security audit or financial outcome was independently certified. The video states that companies can lose money and directs viewers to the current whitepaper and risks. It avoids prices, investment returns and live activity figures.

Narration is synthesized. Captions are timed to generated sentence audio, rather than individual words. Browser compatibility is checked through the H.264/AAC codecs, pixel format, file structure and complete decode; interactive playback in a browser was not available for this run. Frames were visually inspected, including frames extracted from the encoded output.

## Delivery and production sources

The finished MP4 is the deliverable and plays offline without installing any packages. It is uploaded separately from the source bundle. The repository retains the script, captions, artwork, fonts, source snapshots, rendering and audio production scripts, and inspection records.

Large production-only downloads (the FFmpeg distribution, Python wheel archives, pip bootstrap, and neural voice model) are excluded to keep the source upload below 8 MiB. The production scripts in `tools/audio.py` and `tools/render.py` document how the presentation was made; they require NumPy, Pillow, Piper TTS, the LJ Speech high voice model and FFmpeg in their original local build paths. **A self-contained offline rebuild is not included.** No dependency installation or regeneration is needed to inspect the delivered video.

`tools/verify.py` verifies an existing video using FFmpeg and FFprobe, either installed on PATH or available in `.build/ffmpeg/`:

```sh
python3 tools/verify.py
```

The verifier checks codec, duration, dimensions, frame count, AAC sample rate and channels, size, MP4 atom ordering, audible audio levels, and a full error-free decode. It writes `review/ffprobe.json` and `review/verification.json`. These are local measurements, not independent certification. Verification requires those media tools; the video itself does not.

Space Grotesk and JetBrains Mono are bundled with their SIL Open Font Licenses. The synthetic voice used the [Piper LJ Speech high model](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ljspeech/high), with its retained model card at `vendor/VOICE_MODEL_CARD`. The training recordings are [public domain](https://keithito.com/LJ-Speech-Dataset/). Production used FFmpeg 7.0.2, Pillow 13.0.0, NumPy 2.5.4 and Piper TTS 1.8.0.
