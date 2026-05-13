import ast
import json
import tempfile

import pandas as pd
import requests


_PROCESSED_DATASET_ID = "1TyRENYWxCU-kipJR4tDXLFRTbljm4_DR"
_RAW_DATASET_ID = "1o3__6u1eR-VWAGgwOMacQCF96g4wKSfM"


def _download_gdrive(file_id: str, suffix: str) -> str:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(response.content)
        return f.name


def load_processed_candidates() -> pd.DataFrame:
    """
    Load the processed candidates dataset.
    Includes pre-computed Gemini embeddings (3072-dim) and parsed full_experience.
    """
    path = _download_gdrive(_PROCESSED_DATASET_ID, suffix=".csv")
    df = pd.read_csv(path)
    df = df.drop(columns=["embedding_old"], errors="ignore")
    df["embedding"] = df["embedding"].apply(ast.literal_eval)
    df["full_experience"] = df["full_experience"].apply(ast.literal_eval)
    return df


def load_raw_candidates() -> pd.DataFrame:
    """Load the full raw candidates dataset (no embeddings)."""
    path = _download_gdrive(_RAW_DATASET_ID, suffix=".json")
    with open(path) as f:
        return pd.DataFrame(json.load(f))
