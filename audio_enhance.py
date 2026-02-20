# audio_enhance.py
# Goal:
# - Keep the "desktop upload" path working (wav/mp3/m4a that librosa/soundfile can already decode)
# - Fix the "mic recording" path (MediaRecorder webm/opus or mp4) by converting ONLY when needed.

from functools import partial
import io
import subprocess

import numpy as np
import librosa
import scipy.signal as sig
import psola
import soundfile as sf
import imageio_ffmpeg

SEMITONES_IN_OCTAVE = 12


# ✅ Always use the same ffmpeg binary reliably (works even if PATH is weird)
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def _ffmpeg_to_wav_bytes(audio_bytes: bytes, target_sr: int = 16000, mono: bool = True) -> bytes:
    """
    Convert arbitrary audio bytes (webm/opus/mp4/ogg/mp3/wav...) -> WAV PCM 16-bit.
    Uses a known ffmpeg exe (imageio_ffmpeg).
    """
    cmd = [
        FFMPEG_EXE,
        "-hide_banner", "-loglevel", "error",
        "-i", "pipe:0",
        "-f", "wav",
        "-acodec", "pcm_s16le",
        "-ar", str(target_sr),
        "-ac", "1" if mono else "2",
        "pipe:1"
    ]
    p = subprocess.run(cmd, input=audio_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode(errors="ignore")
        raise RuntimeError(f"ffmpeg conversion failed: {err or 'unknown error'}")
    if not p.stdout:
        raise RuntimeError("ffmpeg conversion produced empty output")
    return p.stdout


def _decode_audio_bytes(audio_bytes: bytes):
    """
    Decode audio bytes into (y, sr) safely.

    Strategy:
    1) Try decode directly with soundfile (works for wav/flac/ogg-vorbis etc.)
    2) If it fails, convert to wav with ffmpeg and decode again (fixes webm/opus, mp4, many ogg-opus cases)
    """
    # 1) direct decode attempt (keeps your previous "working upload" behavior)
    try:
        y, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)
        return y, sr
    except Exception:
        pass

    # 2) fallback conversion (mic recordings are usually here)
    wav_bytes = _ffmpeg_to_wav_bytes(audio_bytes, target_sr=16000, mono=True)
    y, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32", always_2d=False)
    return y, sr


def degrees_from(scale: str):
    degrees = librosa.key_to_degrees(scale)
    degrees = np.concatenate((degrees, [degrees[0] + SEMITONES_IN_OCTAVE]))
    return degrees


def closest_pitch(f0):
    midi_note = np.around(librosa.hz_to_midi(f0))
    nan_indices = np.isnan(f0)
    midi_note[nan_indices] = np.nan
    return librosa.midi_to_hz(midi_note)


def closest_pitch_from_scale(f0, scale):
    if np.isnan(f0):
        return np.nan
    degrees = degrees_from(scale)
    midi_note = librosa.hz_to_midi(f0)
    degree = midi_note % SEMITONES_IN_OCTAVE
    degree_id = np.argmin(np.abs(degrees - degree))
    degree_difference = degree - degrees[degree_id]
    midi_note -= degree_difference
    return librosa.midi_to_hz(midi_note)


def aclosest_pitch_from_scale(f0, scale):
    sanitized_pitch = np.zeros_like(f0)
    for i in np.arange(f0.shape[0]):
        sanitized_pitch[i] = closest_pitch_from_scale(f0[i], scale)

    smoothed = sig.medfilt(sanitized_pitch, kernel_size=11)
    smoothed[np.isnan(smoothed)] = sanitized_pitch[np.isnan(sanitized_pitch)]
    return smoothed


def autotune(audio, sr, correction_function, plot=False):
    frame_length = 2048
    hop_length = frame_length // 4
    fmin = librosa.note_to_hz('C2')
    fmax = librosa.note_to_hz('C7')

    # safety: if audio is too short, pyin can fail
    if audio is None or len(audio) < frame_length * 2:
        # return original audio (no crash)
        return audio.astype(np.float32)

    f0, voiced_flag, voiced_probabilities = librosa.pyin(
        audio,
        frame_length=frame_length,
        hop_length=hop_length,
        sr=sr,
        fmin=fmin,
        fmax=fmax
    )

    corrected_f0 = correction_function(f0)

    return psola.vocode(
        audio,
        sample_rate=int(sr),
        target_pitch=corrected_f0,
        fmin=fmin,
        fmax=fmax
    )


def autotune_enhance_audio(audio_data, correction_method='closest', plot=False, scale=None):
    """
    Enhances audio data using auto-tuning.

    audio_data: BytesIO OR raw bytes.
      - Desktop upload: often decodes directly
      - Mic recording: often requires ffmpeg fallback

    Returns: (pitch_corrected_y, sr)
    """
    audio_bytes = audio_data.read() if hasattr(audio_data, "read") else audio_data
    if not audio_bytes:
        raise ValueError("Empty audio received")

    # ✅ decode robustly (direct first, ffmpeg fallback)
    y, sr = _decode_audio_bytes(audio_bytes)

    # Ensure mono
    if isinstance(y, np.ndarray) and y.ndim > 1:
        # could be (n, ch) or (ch, n) depending on decoder; handle both
        if y.shape[0] <= 4 and y.shape[0] < y.shape[1]:
            y = y[0, :]
        else:
            y = y[:, 0]

    # select correction function
    if correction_method == 'closest':
        correction_function = closest_pitch
    else:
        if not scale:
            raise ValueError("scale is required when correction_method is not 'closest'")
        correction_function = partial(aclosest_pitch_from_scale, scale=scale)

    pitch_corrected_y = autotune(y, sr, correction_function, plot).astype(np.float32)
    return pitch_corrected_y, int(sr)
