# NIGHTSHIFT — TV news remix

Delivered video: **[artifacts/video-v2.mp4](artifacts/video-v2.mp4)** (`video/mp4`). The MP4 is intentionally untracked and uploaded separately.

A two-minute TV-style technology feature with two photographic fictional presenters, pixelated newsroom imagery, animated mouths, chapter headlines, a ticker, English captions and cutaways to the original NIGHTSHIFT presentation. The original narration and music continue throughout. The correspondent appears from 01:00 to 01:40; the studio anchor opens and closes the feature.

| Property | Delivery |
| --- | --- |
| Duration | 120 seconds / 2:00 |
| Dimensions | 1280 × 720, landscape 16:9 |
| Frame rate | 24 fps; 2,880 frames |
| Video | H.264, yuv420p, MP4 with faststart |
| Audio | AAC, 48 kHz, stereo, 160 kb/s target |
| File size | 5,218,952 bytes (4.98 MiB) |
| Captions | Burned in; editable news-captions.srt |
| Measurements | review/news-v2-verification.json |
| Visual inspection | review/news-v2-contact.png |

## Production

Two fictional photographic newsroom plates were made with the built-in image generation tool and retained at assets/news-anchor.png and assets/news-correspondent.png. Python and FFmpeg apply speech-driven mouth deformation, nearest-neighbor pixelation, original-video inserts, crisp broadcast typography and captions. No hosted video model or additional dependency installation was used.

Run `python3 tools/news_v2.py` to reproduce the remix offline. It requires Python 3, FFmpeg with libx264/libass, the retained assets and the original separately supplied artifacts/video.mp4. Temporary files go to test/scratch/news/. The original input MP4 is not duplicated into the committed source bundle. The finished output plays independently of all production files.

## Limitations

This is a staged, synthetic news-style presentation, **not footage of real journalists, an actual television broadcast, or independent news endorsement**. The people look photographic but are generated fictional characters. Mouth motion follows narration energy and approximate speech timing; it is stylized animation, not phoneme-accurate lip synchronization or full body performance. A single original synthetic narrator provides audio across both presenter shots; the figures do not have separate recorded voices. No live studio audio was captured. Pixelation is intentional; overlays and captions remain sharp. An on-screen disclosure remains visible throughout.

V2 reuses the earlier project descriptions and original audio without adding current statistics or independently verifying product claims. Original project sources and their limitations remain documented in README.md. No token or deployed contract was changed. FFprobe and a complete FFmpeg decode check the delivered bytes; these local checks do not certify browser playback on every device.

## Checked delivery

`python3 tools/verify_news_v2.py` passed: 120.000 seconds, 2,880 frames, H.264/yuv420p video, AAC stereo audio at 48 kHz, file size below 64 MiB, faststart atom ordering and a complete error-free audio/video decode. Audio measured −20.2 dBFS mean and −1.5 dBFS peak. Eight timeline samples and full-size opening/correspondent frames were visually inspected for layout, pixelation and caption legibility. The local inspection record is retained under review/.
