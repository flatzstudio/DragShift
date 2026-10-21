# DragShift: Audio & Video Fork

This independent fork is based on [llamaboi55/DragShift](https://github.com/llamaboi55/DragShift).
The upstream project and its history are preserved; this fork adds audio and video conversion.
Upstream DragShift is MIT-licensed. See [LICENSE](LICENSE) and the separate FFmpeg terms below.

Convert and edit files on **Windows, Mac and Linux** with a liquid-glass radial menu. Start dragging any file, press **Shift**, and drop it on a slice.

![DragShift radial menu and Add BG editor](docs/preview.png)

## Availability

No fork binary release is published yet. The upstream project's installers and downloads do
not contain this fork's audio/video changes. See [Run from source](#run-from-source) to try
the current code. Binary releases are blocked pending the corresponding-source materials
for the bundled GPL FFmpeg build and a complete dependency license review. In particular,
PyMuPDF is AGPL-3.0-or-commercial and PySide6/Qt has multiple license options; this fork has
not established a commercial grant or completed compliance review. See
[Third-Party Notices](THIRD_PARTY_NOTICES.md). The source is prepared for review, not declared
license-cleared for redistribution as a ready-to-run application.

## How to use

1. Start dragging a supported image, document, audio or video file in File Explorer, Finder, your Linux file manager or on the desktop.
2. Press **Shift**. The menu opens under your cursor.
3. Drop the file on a slice. The result is saved **next to the original**, and the original is never changed.
4. To switch between **Convert** and **Tools**, tap **Shift** again.

Each action ends with a notification that shows what changed, for example *"2.4 MB → 610 KB · 75% smaller"* or *"2400×1600 → 1200×800"*, with **Open**, **Show in folder** and **Undo**. Undo moves the new file to the Recycle Bin (Trash on Mac and Linux).

You can also right-click a file → **DragShift…**, use **Send to → DragShift**, or double-click the tray icon to pick a file.

## What it does

| File | Convert to | Tools |
|---|---|---|
| Images (JPG, PNG, WEBP, HEIC, AVIF, TIFF, BMP, GIF, ICO) | Any of those, or PDF. Several images become one combined PDF | **Compress** (by quality or to a target size such as "under 500 KB", with a before/after preview, several files at once) · **Resize** · **Crop** (ratios, live pixel size, rotate) · **Edit** (Auto, light/colour, rotate, flip, B&W, hold to compare) · **Annotate** (arrows, boxes, numbered steps, text, marker) · **Redact** · **Add BG** · **Metadata** (camera, date, GPS location with a map link; remove location only or remove everything) |
| PDF | JPG or PNG (one per page), DOCX, TXT | Compress · Split · Rotate · Merge (drop several) · **Protect** (AES-256 password) · **Extract images** · Metadata |
| Word (.docx) | PDF (uses Microsoft Word if it's installed, otherwise a built-in renderer), TXT | — |
| Text (.txt, .md, .csv…) | PDF, DOCX | — |
| Audio (MP3, WAV, FLAC, M4A/AAC, AIFF, ALAC, OGG, Opus, WMA) | Any listed audio format | Streaming FFmpeg conversion; results are written beside the source |
| Video (MP4, MOV, MKV, WebM, AVI, M4V) | Any listed container | FFmpeg conversion and audio extraction |

The audio/video rows list recognized input extensions and output choices, not a promise that
every possible codec/stream combination will convert. Unsupported or damaged inputs can fail.
Audio output tested end-to-end on macOS arm64: WAV PCM (16/24-bit and 32-bit float), MP3,
and FLAC. The bundled FFmpeg advertises the encoders needed for the other listed audio
outputs, but those combinations have not all been individually tested. Video container
outputs use FFmpeg's configured encoders; WebM defaults to VP9, while the other containers
default to H.264. Compatibility still depends on the source streams and target container.

**Settings** (tray menu): trigger key (Shift, Ctrl or Alt), where results go (next to the original or a `DragShift` subfolder), JPG/WebP quality, PDF → image resolution, audio quality profile (Low/Medium/High), audio sample rate, WAV bit depth and channel layout, and start at login. Audio `Auto` sample rate omits resampling; WAV `Auto` uses 16-bit PCM. Upsampling does not restore source detail.

## The look

The menu, notifications and windows use real **liquid-glass** rendering. DragShift captures the screen behind each surface and refracts it through the shape. A curved edge bends light, R, G and B bend by slightly different amounts (which gives the rainbow fringe), a highlight runs along the rim facing the light, and the tint adapts to what's behind it so text stays readable. The menu renders on a background thread while it pops in, so it still opens instantly.

## Tested on real desktops

The upstream repository defines Windows, macOS and Linux CI/E2E workflows. This fork has not
yet published fork-specific CI results. Local validation on macOS arm64:

- `python -m pytest -q`: 45 passed, 1 skipped.
- Frozen arm64 app self-test: passed; existing image/PDF/document checks and bundled FFmpeg startup/audio smoke test passed.
- Real bundled-FFmpeg batch conversions: two files each to WAV, MP3 and FLAC; sample rate, channel layout, WAV bit depth and MP3 bitrate inspected in output streams.
- Video output smoke test: MP4, MOV, MKV, WebM, AVI and M4V using a generated short H.264 source. This is a container smoke test, not broad codec/input coverage.

## Support

DragShift is free. If it saves you time, you can leave a tip on Cash App: [**$AtikaKadesha**](https://cash.app/$AtikaKadesha). Thank you!

<img src="docs/tip-cashapp.png" alt="Cash App QR code for $AtikaKadesha" width="220">

## License

[MIT](LICENSE) applies to DragShift's own code. Keep the upstream copyright and permission
notice in copies or substantial portions. The separately bundled FFmpeg executable is
GPL-2.0-or-later; see [Third-Party Notices](THIRD_PARTY_NOTICES.md). The MIT license does
not relicense FFmpeg or other third-party components.

## Run from source

Requirements: Python 3.10 or newer and a supported desktop session. The fork's
media conversions and clean app bundle have been exercised on macOS arm64 only;
Windows, Intel macOS and Linux fork builds have not been validated here.
Most entries in `requirements.txt` are minimum versions rather than exact pins,
so installs can resolve to different versions and license notices over time.
The dependency inventory in [Third-Party Notices](THIRD_PARTY_NOTICES.md) is a
local snapshot, not a complete cross-platform bill of materials.

```bash
pip install -r requirements.txt
python -m dragshift
```

On Linux, PySide6 also needs the Qt XCB libraries: `sudo apt install libxcb-cursor0 libxkbcommon-x11-0`.

Tests: `python -m pytest -q`. Logs are written to `%LOCALAPPDATA%\DragShift\log.txt` on Windows, `~/Library/Logs/DragShift/log.txt` on Mac and `~/.local/share/DragShift/log.txt` on Linux.

### Audio and video codecs

The pinned FFmpeg provider is `imageio-ffmpeg==0.6.0` (FFmpeg 7.1). The
macOS arm64 binary is bundled into the app, so the user does not need Homebrew
or a system FFmpeg. The binary advertises H.264 (`libx264`), HEVC
(`libx265`), VP9 (`libvpx-vp9`), AV1 (`libsvtav1`/`libaom`), MP3, AAC, FLAC,
ALAC, Vorbis, Opus, PCM and WMA encoders. These are binary capabilities; the
app currently exposes H.264 for most video containers and VP9 for WebM, not a
general video codec selector. WMA output uses WMA v2.
See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md): the actual binary reports
GNU GPL version 2 or later (`--enable-gpl`), not GPLv3. The exact corresponding
source bundle, including external library sources and build/install scripts, is
not yet prepared. Do not redistribute an app bundle containing this FFmpeg until
the compliance materials have been assembled and reviewed.

Audio and video conversions run as FFmpeg subprocesses and do not load media
files into Python memory. Audio Settings are persisted using QSettings and
applied to single-file and batch conversions. Batch conversions continue after
individual file errors and choose a non-conflicting output name. Current
limitations: there is no video codec/quality selector (WebM defaults to VP9;
other targets default to H.264/Balanced);
live per-file progress and cancellation controls, automatic container-aware
remux selection, subtitle/multitrack selection, and a dedicated conversion
report window are not implemented. Video encoding uses FFmpeg software encoders;
hardware VideoToolbox encoding is not currently selected. The app includes
FFmpeg but not a separate ffprobe binary.

No fork installer, signing or notarization workflow is currently published.
