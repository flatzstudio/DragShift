from pathlib import Path
import re
import subprocess

import pytest
from PySide6.QtCore import QSettings

from dragshift import media, settings
from dragshift.util import category


def test_media_categories_and_formats():
    assert category("音楽 file.wav") == "audio"
    assert category("clip.MOV") == "video"
    assert len(media.AUDIO_FORMATS) == 10
    assert {"MP4", "MOV", "MKV", "WEBM", "AVI", "M4V"} == set(media.VIDEO_FORMATS)


def test_audio_command_respects_format_specific_options(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "ffmpeg_path", lambda: Path("/bundled/ffmpeg"))
    cmd = media.build_command("in file.wav", tmp_path / "out.mp3", "audio", "MP3", bitrate=256,
                              sample_rate=48000)
    assert cmd[cmd.index("-i") + 1] == "in file.wav"
    assert "libmp3lame" in cmd and "256k" in cmd and "48000" in cmd
    wav = media.build_command("in.wav", "out.wav", "audio", "WAV", pcm_bits=24)
    assert "pcm_s24le" in wav and "-b:a" not in wav


@pytest.mark.parametrize("profile,bitrates", [
    ("Low", {"MP3": 128, "M4A": 128, "OPUS": 96, "OGG": 128}),
    ("Medium", {"MP3": 192, "M4A": 192, "OPUS": 128, "OGG": 192}),
    ("High", {"MP3": 320, "M4A": 256, "OPUS": 192, "OGG": 256}),
])
def test_quality_profiles_map_to_encoder_bitrates(profile, bitrates, tmp_path, monkeypatch):
    monkeypatch.setattr(media, "ffmpeg_path", lambda: Path("/bundled/ffmpeg"))
    for target, bitrate in bitrates.items():
        cmd = media.build_command("source.wav", tmp_path / "out", "audio", target,
                                  audio=media.AudioConfig(quality=profile))
        assert cmd[cmd.index("-b:a") + 1] == f"{bitrate}k"


@pytest.mark.parametrize(("depth", "codec"), [("auto", "pcm_s16le"), ("16", "pcm_s16le"),
                                                 ("24", "pcm_s24le"), ("32f", "pcm_f32le")])
def test_wav_depth_and_other_audio_options(depth, codec, tmp_path, monkeypatch):
    monkeypatch.setattr(media, "ffmpeg_path", lambda: Path("/bundled/ffmpeg"))
    cmd = media.build_command("source.wav", tmp_path / "out.wav", "audio", "WAV",
                              audio=media.AudioConfig(wav_bit_depth=depth, sample_rate=96000,
                                                      channels="mono"))
    assert codec in cmd
    assert cmd[cmd.index("-ar") + 1] == "96000"
    assert cmd[cmd.index("-ac") + 1] == "1"


def test_settings_defaults_validation_and_persistence(tmp_path):
    path = tmp_path / "settings.ini"
    q = QSettings(str(path), QSettings.IniFormat)
    first = settings.Settings(q)
    first.apply()
    assert first.audio_config == media.AudioConfig()
    first.set("audio_quality", "Low")
    first.set("audio_sample_rate", "48000")
    first.set("audio_wav_bit_depth", "24")
    first.set("audio_channels", "stereo")
    restored = settings.Settings(QSettings(str(path), QSettings.IniFormat))
    restored.apply()
    assert restored.audio_config == media.AudioConfig("Low", 48000, "24", "stereo")
    restored.q.setValue("audio_quality", "nonsense")
    restored.q.setValue("audio_channels", "surround")
    restored.apply()
    assert restored.audio_config.quality == "High"
    assert restored.audio_config.channels == "auto"


def _ffmpeg_details(path):
    result = subprocess.run([str(media.ffmpeg_path()), "-hide_banner", "-i", str(path), "-f", "null", "-"],
                            capture_output=True, text=True)
    return result.stderr


@pytest.mark.parametrize(("depth", "codec"), [("16", "pcm_s16le"), ("24", "pcm_s24le"),
                                                 ("32f", "pcm_f32le")])
@pytest.mark.parametrize(("channels", "channel_label"), [("mono", "mono"), ("stereo", "stereo")])
def test_real_ffmpeg_wav_depth_channels_sample_rate(tmp_path, depth, codec, channels, channel_label):
    ffmpeg = str(media.ffmpeg_path())
    src = tmp_path / "источник tone.wav"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                    "sine=frequency=440:sample_rate=44100:duration=0.25", "-ac", "2", str(src)], check=True)
    out = media.convert_one(src, "WAV", "audio", audio=media.AudioConfig(
        wav_bit_depth=depth, sample_rate=48000, channels=channels))
    info = _ffmpeg_details(out)
    assert codec in info and "48000 Hz" in info
    assert re.search(rf"48000 Hz, {channel_label}", info)
    assert src.is_file() and src.stat().st_size > 0


def test_real_ffmpeg_profiles_batch_and_no_overwrite(tmp_path):
    ffmpeg = str(media.ffmpeg_path())
    sources = [tmp_path / "tone one.wav", tmp_path / "тон два.wav"]
    for src in sources:
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                        "sine=frequency=440:duration=0.25", str(src)], check=True)
    first_out, errors = media.convert_batch(sources, "MP3", "audio",
                                            audio=media.AudioConfig(quality="Low"))
    assert not errors and len(first_out) == 2
    assert all("128 kb/s" in _ffmpeg_details(path) for path in first_out)
    second_out, errors = media.convert_batch(sources, "MP3", "audio",
                                             audio=media.AudioConfig(quality="High"))
    assert not errors and len(second_out) == 2
    assert all(path.exists() for path in first_out + second_out)
    assert all(path != original for path, original in zip(second_out, first_out))
    assert all(source.is_file() for source in sources)


def test_video_command_and_remux(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "ffmpeg_path", lambda: Path("/bundled/ffmpeg"))
    encode = media.build_command("in.mov", tmp_path / "out.mp4", "video", "MP4", codec="H.264")
    assert "libx264" in encode and "-crf" in encode
    remux = media.build_command("in.mkv", tmp_path / "out.mp4", "video", "MP4", remux=True)
    assert "copy" in remux and "libx264" not in remux
    webm = media.build_command("in.mp4", tmp_path / "out.webm", "video", "WEBM", codec="VP9")
    assert "libvpx-vp9" in webm and "libopus" in webm
    default_webm = media.build_command("in.mp4", tmp_path / "default.webm", "video", "WEBM")
    assert "libvpx-vp9" in default_webm


def test_batch_keeps_going_after_bad_input(tmp_path, monkeypatch):
    files = [tmp_path / "one.wav", tmp_path / "bad.wav", tmp_path / "three.wav"]
    for path in files:
        path.touch()
    def run(src, target, kind, **kwargs):
        if Path(src).name == "bad.wav":
            raise ValueError("bad input")
        return Path(src).with_suffix(".mp3")
    monkeypatch.setattr(media, "convert_one", run)
    outs, errors = media.convert_batch(files, "MP3", "audio")
    assert [p.stem for p in outs] == ["one", "three"]
    assert len(errors) == 1 and errors[0][0] == files[1]


@pytest.mark.parametrize("target", ["WMA", "OPUS", "ALAC"])
def test_audio_command_has_no_fake_bitrate_for_lossless_or_specific(target, tmp_path, monkeypatch):
    monkeypatch.setattr(media, "ffmpeg_path", lambda: Path("/bundled/ffmpeg"))
    cmd = media.build_command("in", tmp_path / "out", "audio", target)
    if target in ("WMA", "OPUS"):
        assert "-b:a" in cmd
    else:
        assert "-b:a" not in cmd


def test_lossless_codecs_ignore_lossy_quality():
    for target in ("FLAC", "ALAC"):
        cmd = media.build_command("in.wav", "out", "audio", target,
                                  audio=media.AudioConfig(quality="Low"))
        assert "-b:a" not in cmd


def test_broken_input_is_reported_and_never_overwrites(tmp_path):
    src = tmp_path / "corrupt.wav"
    src.write_bytes(b"not an audio stream")
    existing = tmp_path / "corrupt.mp3"
    existing.write_bytes(b"keep this result")
    with pytest.raises(Exception, match="FFmpeg could not convert"):
        media.convert_one(src, "MP3", "audio")
    assert src.read_bytes() == b"not an audio stream"
    assert existing.read_bytes() == b"keep this result"
    assert (tmp_path / "corrupt (1).mp3").exists() is False
