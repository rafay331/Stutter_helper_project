# dysarthria_inference.py

import numpy as np
import librosa
import joblib
from pathlib import Path

FRAME_SIZE = 1024
HOP_SIZE = 512
DESIRED_LENGTH = 1000

BASE_DIR = Path(__file__).resolve().parent

# Load models once
model = joblib.load(BASE_DIR / "rf_zero_crossing_model.joblib")
scaler = joblib.load(BASE_DIR / "zc_scaler.joblib")
label_encoder = joblib.load(BASE_DIR / "label_encoder.joblib")


def extract_zero_crossing(filepath):
    """Extract fixed-length zero-crossing features from a WAV file."""
    y, sr = librosa.load(filepath, sr=None)

    zc = librosa.feature.zero_crossing_rate(
        y=y, frame_length=FRAME_SIZE, hop_length=HOP_SIZE
    )[0]

    if len(zc) < DESIRED_LENGTH:
        zc = np.pad(zc, (0, DESIRED_LENGTH - len(zc)))
    else:
        zc = zc[:DESIRED_LENGTH]

    return np.array(zc).reshape(1, -1)


def predict_dysarthria(filepath):
    """Returns label: 'Dysarthric' or 'Non-Dysarthric'"""
    features = extract_zero_crossing(filepath)
    features_scaled = scaler.transform(features)
    pred = model.predict(features_scaled)
    label = label_encoder.inverse_transform(pred)[0]
    return label
