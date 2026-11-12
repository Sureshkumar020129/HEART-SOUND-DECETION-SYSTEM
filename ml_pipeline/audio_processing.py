"""
audio_processing.py
-------------------
Heart sound audio loading, validation, resampling, normalization,
and spectrogram/waveform generation.

All functions raise descriptive exceptions so the caller can surface
meaningful error messages to the user — never swallow errors silently.
"""

import io
import base64
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import librosa
import librosa.display
import soundfile as sf

logger = logging.getLogger(__name__)

TARGET_SR = 22050          # Training sample rate
AUDIO_DURATION = 5         # seconds to use from each recording
MIN_DURATION = 1.0         # minimum acceptable recording length (seconds)
MAX_DURATION = 300.0       # maximum (5 minutes)


class AudioProcessingError(Exception):
    """Raised for recoverable audio validation / processing failures."""
    pass


def load_and_validate_audio(file_path: str) -> tuple:
    """
    Load an audio file and return (audio_array, sample_rate).

    Performs:
      - Format validation and decoding (soundfile or librosa/audioread)
      - Duration check
      - Stereo-to-mono conversion
    
    Raises AudioProcessingError on any failure.
    """
    audio = None
    sr = None

    try:
        audio, sr = librosa.load(file_path, sr=None, mono=True)
    except Exception as exc:
        try:
            info = sf.info(file_path)
            data, sr = sf.read(file_path)
            audio = data.mean(axis=1) if data.ndim > 1 else data
        except Exception as exc2:
            raise AudioProcessingError(
                f"Failed to decode audio file: {exc}. "
                "Supported formats: WAV, FLAC, MP3, OGG, AIFF, WEBM."
            )

    if audio is None or len(audio) == 0:
        raise AudioProcessingError("Audio file appears to be empty after decoding.")

    duration = len(audio) / sr
    if duration < MIN_DURATION:
        raise AudioProcessingError(
            f"Recording is too short ({duration:.1f}s). "
            f"Please provide at least {MIN_DURATION} second(s) of audio."
        )
    if duration > MAX_DURATION:
        raise AudioProcessingError(
            f"Recording is too long ({duration:.1f}s). "
            f"Maximum supported duration is {MAX_DURATION / 60:.0f} minutes."
        )

    if np.all(audio == 0):
        raise AudioProcessingError(
            "Recording contains only silence. "
            "Please check your microphone or audio file."
        )

    logger.info(f"Loaded audio: {file_path}, sr={sr}, duration={len(audio)/sr:.2f}s, mono")
    return audio, sr


def resample_audio(audio: np.ndarray, original_sr: int, target_sr: int = TARGET_SR) -> np.ndarray:
    """Resample audio to the model's expected sample rate."""
    if original_sr == target_sr:
        return audio
    try:
        resampled = librosa.resample(audio, orig_sr=original_sr, target_sr=target_sr)
        logger.info(f"Resampled {original_sr}Hz → {target_sr}Hz")
        return resampled
    except Exception as exc:
        raise AudioProcessingError(f"Resampling failed: {exc}")


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """Normalize audio amplitude to [-1, 1]."""
    peak = np.max(np.abs(audio))
    if peak < 1e-8:
        raise AudioProcessingError(
            "Audio signal has near-zero amplitude after loading. "
            "The recording may be silent or corrupted."
        )
    return audio / peak


def pad_or_trim(audio: np.ndarray, sr: int, duration: float = AUDIO_DURATION) -> np.ndarray:
    """Trim or zero-pad audio to exactly `duration` seconds."""
    target_length = int(sr * duration)
    if len(audio) >= target_length:
        return audio[:target_length]
    # Pad with zeros
    padding = target_length - len(audio)
    return np.concatenate([audio, np.zeros(padding)])


def preprocess_audio(file_path: str) -> dict:
    """
    Full preprocessing pipeline.

    Returns a dict with:
      - audio: normalized, resampled, fixed-length np.ndarray
      - sample_rate: int (TARGET_SR)
      - original_sr: int
      - duration_seconds: float (original)
      - channels: int (from soundfile info)
    """
    info = None
    try:
        info = sf.info(file_path)
    except Exception:
        pass

    audio, orig_sr = load_and_validate_audio(file_path)
    duration = len(audio) / orig_sr
    channels = info.channels if info else 1

    audio = resample_audio(audio, orig_sr, TARGET_SR)
    audio = normalize_audio(audio)
    audio = pad_or_trim(audio, TARGET_SR, AUDIO_DURATION)

    return {
        'audio': audio,
        'sample_rate': TARGET_SR,
        'original_sr': orig_sr,
        'duration_seconds': duration,
        'channels': channels,
    }


def generate_waveform_image(audio: np.ndarray, sr: int) -> str:
    """
    Generate a waveform plot and return it as a base64-encoded PNG string.
    """
    fig, ax = plt.subplots(figsize=(10, 2.5))
    times = np.linspace(0, len(audio) / sr, len(audio))
    ax.plot(times, audio, color='#00d4ff', linewidth=0.5, alpha=0.9)
    ax.set_facecolor('#0a1628')
    fig.patch.set_facecolor('#0a1628')
    ax.set_xlabel('Time (s)', color='#a0aec0', fontsize=9)
    ax.set_ylabel('Amplitude', color='#a0aec0', fontsize=9)
    ax.tick_params(colors='#a0aec0', labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor('#2d3748')
    ax.set_title('Heart Sound Waveform', color='#e2e8f0', fontsize=11, pad=8)
    ax.set_xlim(0, len(audio) / sr)
    ax.set_ylim(-1.1, 1.1)
    ax.axhline(0, color='#2d3748', linewidth=0.5, linestyle='--')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def generate_spectrogram_image(audio: np.ndarray, sr: int) -> str:
    """
    Generate a mel-spectrogram plot and return as base64-encoded PNG.
    """
    fig, ax = plt.subplots(figsize=(10, 3))
    mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    img = librosa.display.specshow(
        mel_spec_db, sr=sr, x_axis='time', y_axis='mel',
        fmax=8000, ax=ax, cmap='plasma'
    )
    fig.colorbar(img, ax=ax, format='%+2.0f dB')
    ax.set_title('Mel Spectrogram', color='#e2e8f0', fontsize=11)
    ax.set_facecolor('#0a1628')
    fig.patch.set_facecolor('#0a1628')
    ax.tick_params(colors='#a0aec0', labelsize=8)
    ax.set_xlabel('Time (s)', color='#a0aec0', fontsize=9)
    ax.set_ylabel('Frequency (Hz)', color='#a0aec0', fontsize=9)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')
