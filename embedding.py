# =========================
# Imports
# =========================
from typing import TypeVar, Type, Union, Dict, List
import numpy as np

from pydantic import BaseModel
from google.colab import userdata

from google import genai
from google.adk import Agent
from google.adk.tools import google_search


# =========================
# Auth
# =========================
GOOGLE_API_KEY = userdata.get("GOOGLE_API_KEY")

google_client = genai.Client(
    api_key=GOOGLE_API_KEY
)


# =========================
# Default model
# =========================
MODEL_NAME = "gemini-2.5-flash"


def embed(text: str) -> list[float]:
    response = google_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return response.embeddings[0].values

def embed_batch(texts: list[str]) -> list[list[float]]:
    response = google_client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts
    )
    return [e.values for e in response.embeddings]
