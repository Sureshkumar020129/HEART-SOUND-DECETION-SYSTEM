"""
feature_extraction.py
----------------------
Extracts audio features from a preprocessed heart-sound signal.

Features extracted:
  - MFCCs (mean + std of each coefficient)
  - Chroma features (mean + std)
  - Spectral contrast (mean + std)
  - Zero-crossing rate (mean + std)
  - RMS energy (mean + std)
  - Mel-filterbank energies (mean)
  - Spectral centroid and bandwidth (mean + std)

All features are concatenated into a single 1D feature vector.
"""

import logging
import numpy as np
import librosa

logger = logging.getLogger(__name__)

N_MFCC = 40
N_MELS = 64
N_CHROMA = 12
N_CONTRAST = 7
HOP_LENGTH = 512
N_FFT = 2048


class FeatureExtractionError(Exception):
    """Raised when features cannot be extracted from the audio."""
    pass


def extract_mfcc_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """Extract MFCC mean and std vectors."""
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=N_MFCC,
                                  hop_length=HOP_LENGTH, n_fft=N_FFT)
    return np.concatenate([mfccs.mean(axis=1), mfccs.std(axis=1)])  # 80 features


def extract_chroma_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """Extract chroma mean and std vectors."""
    chroma = librosa.feature.chroma_stft(y=audio, sr=sr, hop_length=HOP_LENGTH, n_fft=N_FFT)
    return np.concatenate([chroma.mean(axis=1), chroma.std(axis=1)])  # 24 features


def extract_spectral_contrast(audio: np.ndarray, sr: int) -> np.ndarray:
    """Extract spectral contrast mean and std."""
    contrast = librosa.feature.spectral_contrast(y=audio, sr=sr,
                                                  hop_length=HOP_LENGTH, n_fft=N_FFT)
    return np.concatenate([contrast.mean(axis=1), contrast.std(axis=1)])  # 14 features


def extract_spectral_shape(audio: np.ndarray, sr: int) -> np.ndarray:
    """Extract spectral centroid and bandwidth mean+std."""
    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr,
                                                  hop_length=HOP_LENGTH, n_fft=N_FFT)
    bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr,
                                                    hop_length=HOP_LENGTH, n_fft=N_FFT)
    return np.array([
        centroid.mean(), centroid.std(),
        bandwidth.mean(), bandwidth.std()
    ])  # 4 features


def extract_temporal_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """Extract ZCR and RMS energy mean+std."""
    zcr = librosa.feature.zero_crossing_rate(audio, hop_length=HOP_LENGTH)
    rms = librosa.feature.rms(y=audio, hop_length=HOP_LENGTH)
    return np.array([
        zcr.mean(), zcr.std(),
        rms.mean(), rms.std()
    ])  # 4 features


def extract_mel_energies(audio: np.ndarray, sr: int) -> np.ndarray:
    """Extract mean mel-filterbank energies."""
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=N_MELS,
                                          hop_length=HOP_LENGTH, n_fft=N_FFT)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    return mel_db.mean(axis=1)  # N_MELS features


def extract_all_features(audio: np.ndarray, sr: int) -> np.ndarray:
    """
    Extract the full feature vector from a preprocessed audio signal.

    Returns a 1D np.ndarray.
    Raises FeatureExtractionError on failure.
    """
    if audio is None or len(audio) == 0:
        raise FeatureExtractionError("Cannot extract features from an empty audio signal.")

    if np.all(audio == 0):
        raise FeatureExtractionError(
            "Audio signal is all zeros. Feature extraction aborted."
        )

    try:
        mfcc = extract_mfcc_features(audio, sr)         # 80
        chroma = extract_chroma_features(audio, sr)     # 24
        contrast = extract_spectral_contrast(audio, sr) # 14
        shape = extract_spectral_shape(audio, sr)       # 4
        temporal = extract_temporal_features(audio, sr) # 4
        mel = extract_mel_energies(audio, sr)           # 64

        features = np.concatenate([mfcc, chroma, contrast, shape, temporal, mel])

        if np.any(np.isnan(features)) or np.any(np.isinf(features)):
            raise FeatureExtractionError(
                "Feature extraction produced NaN or Inf values. "
                "The audio may be too noisy or corrupt."
            )

        logger.info(f"Extracted feature vector of length {len(features)}")
        return features

    except FeatureExtractionError:
        raise
    except Exception as exc:
        raise FeatureExtractionError(f"Unexpected error during feature extraction: {exc}")


def get_feature_summary(features: np.ndarray) -> dict:
    """Return a brief statistical summary of the feature vector for auditing."""
    return {
        'feature_length': int(len(features)),
        'mean': float(np.mean(features)),
        'std': float(np.std(features)),
        'min': float(np.min(features)),
        'max': float(np.max(features)),
    }
