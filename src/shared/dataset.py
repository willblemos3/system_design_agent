import ast
import json
import tempfile
from pathlib import Path

import pandas as pd
import requests


_PROCESSED_DATASET_ID = "1TyRENYWxCU-kipJR4tDXLFRTbljm4_DR"
_RAW_DATASET_ID = "1o3__6u1eR-VWAGgwOMacQCF96g4wKSfM"
_EXPERIENCES_DATASET = "1byTeIm_WvU2ca_jV9-zRohowfi9vS42S/view?usp=sharing"

# repo_root/data/ — checked before any network call
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _download_gdrive(file_id: str, suffix: str) -> str:
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(response.content)
        return f.name


def load_processed_candidates() -> pd.DataFrame:
    """
    Load the processed candidates dataset (full_experience + embeddings).
    Checks data/processed_candidates.json first; falls back to Google Drive.
    """
    local = _DATA_DIR / "processed_candidates.json"
    if local.exists():
        print(f"[dataset] loading from {local}")
        with open(local, encoding="utf-8") as f:
            df = pd.DataFrame(json.load(f))
        if "embedding" in df.columns and isinstance(df["embedding"].iloc[0], str):
            df["embedding"] = df["embedding"].apply(ast.literal_eval)
        if "full_experience" in df.columns and isinstance(df["full_experience"].iloc[0], str):
            df["full_experience"] = df["full_experience"].apply(ast.literal_eval)
        return df

    print("[dataset] local file not found — downloading from Google Drive")
    path = _download_gdrive(_PROCESSED_DATASET_ID, suffix=".csv")
    df = pd.read_csv(path)
    df = df.drop(columns=["embedding_old"], errors="ignore")
    df["embedding"] = df["embedding"].apply(ast.literal_eval)
    df["full_experience"] = df["full_experience"].apply(ast.literal_eval)
    return df


def load_experiences() -> pd.DataFrame:
    """
    Load the experiences dataset (one row per work experience, with embedded_content).
    Requires feature_engineering_workshop to have been run first.
    Checks data/experiences.json — no remote fallback (generated locally).
    """
    local = _DATA_DIR / "experiences.json"
    if not local.exists():
        raise FileNotFoundError(
            f"{local} not found. Run notebooks/workshops/feature_engineering_workshop.ipynb first."
        )
    print(f"[dataset] loading from {local}")
    with open(local, encoding="utf-8") as f:
        df = pd.DataFrame(json.load(f))
    if "embedded_content" in df.columns and isinstance(df["embedded_content"].iloc[0], str):
        df["embedded_content"] = df["embedded_content"].apply(ast.literal_eval)
    if "experience" in df.columns and isinstance(df["experience"].iloc[0], str):
        df["experience"] = df["experience"].apply(ast.literal_eval)
    return df


def load_raw_candidates() -> pd.DataFrame:
    """
    Load the raw candidates dataset (no embeddings).
    Checks data/raw_candidates.json first; falls back to Google Drive.
    """
    local = _DATA_DIR / "raw_candidates.json"
    if local.exists():
        print(f"[dataset] loading from {local}")
        with open(local, encoding="utf-8") as f:
            return pd.DataFrame(json.load(f))

    print("[dataset] local file not found — downloading from Google Drive")
    path = _download_gdrive(_RAW_DATASET_ID, suffix=".json")
    with open(path) as f:
        return pd.DataFrame(json.load(f))
