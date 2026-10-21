"""Streaming audio/video conversion through the bundled FFmpeg executable."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .util import UserError, unique_path

AUDIO_FORMATS = {
    "MP3": (".mp3", "libmp3lame", "mp3"),
    "WAV": (".wav", "pcm_s16le", "wav"),
    "FLAC": (".flac", "flac", "flac"),
    "M4A": (".m4a", "aac", "ipod"),
    "AAC": (".aac", "aac", "adts"),
    "AIFF": (".aiff", "pcm_s16be", "aiff"),
    "ALAC": (".m4a", "alac", "ipod"),
    "OGG": (".ogg", "libvorbis", "ogg"),
    "OPUS": (".opus", "libopus", "opus"),
    "WMA": (".wma", "wmav2", "asf"),
}
VIDEO_FORMATS = {"MP4": (".mp4", "mp4"), "MOV": (".mov", "mov"), "MKV": (".mkv", "matroska"),
                 "WEBM": (".webm", "webm"), "AVI": (".avi", "avi"), "M4V": (".m4v", "ipod")}
VIDEO_CODECS = {"H.264": "libx264", "H.265": "libx265", "VP9": "libvpx-vp9", "AV1": "libsvtav1"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".aiff", ".aif", ".ogg", ".opus", ".wma"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
QUALITY_BITRATES = {
    "Low": {"MP3": 128, "AAC": 128, "M4A": 128, "OPUS": 96, "OGG": 128, "WMA": 96},
    "Medium": {"MP3": 192, "AAC": 192, "M4A": 192, "OPUS": 128, "OGG": 192, "WMA": 128},
    "High": {"MP3": 320, "AAC": 256, "M4A": 256, "OPUS": 192, "OGG": 256, "WMA": 192},
}


@dataclass(frozen=True)
class AudioConfig:
    quality: str = "High"
    sample_rate: int | None = None
    wav_bit_depth: str = "auto"
    channels: str = "auto"


def ffmpeg_path() -> Path:
    """Resolve FFmpeg from the PyInstaller app bundle or pinned imageio-ffmpeg package."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    bundle_tools = root / "ffmpeg"
    candidates = [bundle_tools / "ffmpeg", bundle_tools / "ffmpeg.exe"]
    if bundle_tools.is_dir():
        candidates.extend(p for p in bundle_tools.iterdir() if p.name.startswith("ffmpeg"))
    if getattr(sys, "frozen", False):
        exe_tools = Path(sys.executable).parent / "ffmpeg"
        candidates += [exe_tools / "ffmpeg", exe_tools / "ffmpeg.exe"]
        if exe_tools.is_dir():
            candidates.extend(p for p in exe_tools.iterdir() if p.name.startswith("ffmpeg"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    try:
        import imageio_ffmpeg
        candidate = Path(imageio_ffmpeg.get_ffmpeg_exe())
        if candidate.is_file():
            return candidate
    except Exception:
        pass
    raise UserError("The bundled FFmpeg tool is missing. Reinstall DragShift.")


def probe(path: str | Path) -> dict:
    exe = ffmpeg_path()
    try:
        result = subprocess.run([str(exe), "-hide_banner", "-i", str(path), "-f", "ffmetadata", "-"],
                                capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise UserError("FFmpeg could not inspect this media file.") from e
    if "Input #" not in result.stderr:
        raise UserError("This media file is unsupported or damaged.")
    # ffprobe is included with our bundle when available; FFmpeg stderr is a safe fallback.
    ffprobe = exe.with_name("ffprobe")
    if ffprobe.exists():
        p = subprocess.run([str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                           capture_output=True, text=True)
        if p.returncode == 0:
            return json.loads(p.stdout)
    # imageio-ffmpeg intentionally ships only ffmpeg; retain useful stream data from its
    # diagnostic output instead of assuming an unrelated ffprobe binary exists.
    return {"streams": result.stderr, "format": {"filename": str(path)}}


def audio_targets(path: str | Path) -> list[str]:
    return [name for name, (ext, _, _) in AUDIO_FORMATS.items() if Path(path).suffix.lower() != ext]


def video_targets(path: str | Path) -> list[str]:
    return [name for name, (ext, _) in VIDEO_FORMATS.items() if Path(path).suffix.lower() != ext]


def build_command(src: str | Path, dst: str | Path, kind: str, target: str, *, bitrate: int = 192,
                  sample_rate: int | None = None, pcm_bits: int = 16, codec: str = "H.264",
                  quality: str = "Balanced", extract_audio: bool = False, remux: bool = False,
                  audio: AudioConfig | None = None) -> list[str]:
    exe = str(ffmpeg_path())
    args = [exe, "-hide_banner", "-nostdin", "-y", "-i", str(src), "-map_metadata", "0"]
    if kind == "audio" or extract_audio:
        target = target.upper()
        ext, encoder, muxer = AUDIO_FORMATS[target]
        args += ["-vn", "-map", "0:a:0"]
        if encoder in {"libmp3lame", "aac", "libvorbis", "libopus", "wmav2"}:
            if audio is not None:
                bitrate = QUALITY_BITRATES[audio.quality][target]
            args += ["-c:a", encoder, "-b:a", f"{bitrate}k"]
        else:
            args += ["-c:a", encoder]
        if audio is not None:
            sample_rate = audio.sample_rate
            if target == "WAV":
                pcm_bits = {"auto": 16, "16": 16, "24": 24, "32f": 32}[audio.wav_bit_depth]
            if audio.channels in ("mono", "stereo"):
                args += ["-ac", "1" if audio.channels == "mono" else "2"]
        if sample_rate:
            args += ["-ar", str(sample_rate)]
        if target.upper() == "WAV":
            wav_codecs = {16: "pcm_s16le", 24: "pcm_s24le", 32: "pcm_f32le"}
            if pcm_bits not in wav_codecs:
                raise ValueError("WAV bit depth must be 16, 24, or 32-bit float")
            args[args.index("pcm_s16le")] = wav_codecs[pcm_bits]
        args += ["-f", muxer]
    else:
        ext, muxer = VIDEO_FORMATS[target.upper()]
        if remux:
            args += ["-map", "0", "-c", "copy"]
        else:
            if target.upper() == "WEBM" and codec == "H.264":
                codec = "VP9"
            encoder = VIDEO_CODECS[codec]
            args += ["-map", "0:v:0", "-map", "0:a?", "-map", "0:s?", "-c:v", encoder]
            preset = {"Fast": "ultrafast", "Balanced": "medium", "Best": "slow"}[quality]
            if encoder in ("libx264", "libx265"):
                args += ["-preset", preset, "-crf", {"Fast": "26", "Balanced": "21", "Best": "18"}[quality]]
            elif encoder == "libvpx-vp9":
                args += ["-deadline", "good", "-cpu-used", {"Fast": "6", "Balanced": "2", "Best": "0"}[quality],
                         "-crf", {"Fast": "36", "Balanced": "31", "Best": "24"}[quality], "-b:v", "0"]
            else:
                args += ["-preset", {"Fast": "10", "Balanced": "7", "Best": "4"}[quality],
                         "-crf", {"Fast": "38", "Balanced": "32", "Best": "24"}[quality]]
            audio_codec = {"WEBM": "libopus", "MP4": "aac", "M4V": "aac", "MOV": "aac",
                           "AVI": "libmp3lame", "MKV": "copy"}[target.upper()]
            args += ["-c:a", audio_codec]
        args += ["-f", muxer]
    args += ["-progress", "pipe:1", "-nostats", str(dst)]
    return args


class ConversionCancelled(Exception):
    pass


def convert_one(src: str | Path, target: str, kind: str, *, cancel: threading.Event | None = None,
                progress: Callable[[float], None] | None = None, audio: AudioConfig | None = None,
                **options) -> Path:
    src = Path(src)
    extract_audio = bool(options.pop("extract_audio", False))
    if kind == "audio" or extract_audio:
        ext = AUDIO_FORMATS[target.upper()][0]
    else:
        ext = VIDEO_FORMATS[target.upper()][0]
    dst = unique_path(src.with_suffix(ext))
    try:
        fd = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    except FileExistsError:
        dst = unique_path(src.with_suffix(ext))
        fd = os.open(dst, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    tmp = dst.with_name(f".{dst.stem}.{uuid.uuid4().hex}.part{ext}")
    try:
        cmd = build_command(src, tmp, "audio" if extract_audio else kind, target,
                            extract_audio=extract_audio, audio=audio, **options)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        assert p.stdout is not None
        for line in p.stdout:
            if cancel and cancel.is_set():
                p.terminate()
                p.wait(timeout=5)
                raise ConversionCancelled()
            if line.startswith("out_time_ms=") and progress:
                progress(0.0)  # progress is defined per process when duration is unavailable
        stderr = p.stderr.read() if p.stderr else ""
        if p.wait() != 0:
            dst.unlink(missing_ok=True)
            low = stderr.lower()
            if "no space left" in low:
                message = "Not enough free disk space."
            elif "matches no streams" in low or "does not contain any stream" in low:
                message = "This file has no audio stream to convert."
            else:
                message = "FFmpeg could not convert this file with the selected format/settings."
            raise UserError(message)
        os.replace(tmp, dst)
        return dst
    except OSError as e:
        raise UserError("FFmpeg could not start. Reinstall DragShift.") from e
    finally:
        if tmp.exists():
            tmp.unlink()
        if dst.exists() and dst.stat().st_size == 0:
            dst.unlink()


def convert_batch(paths: list[str | Path], target: str, kind: str, *, cancel: threading.Event | None = None,
                  progress: Callable[[int, int, Path], None] | None = None,
                  audio: AudioConfig | None = None, **options) -> tuple[list[Path], list[tuple[Path, str]]]:
    successes, errors = [], []
    for i, src in enumerate(paths, 1):
        if cancel and cancel.is_set():
            break
        try:
            successes.append(convert_one(src, target, kind, cancel=cancel, audio=audio, **options))
        except ConversionCancelled:
            break
        except Exception as e:
            errors.append((Path(src), str(e)))
        if progress:
            progress(i, len(paths), Path(src))
    return successes, errors
