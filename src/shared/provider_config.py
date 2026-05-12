from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ProviderEntry:
    name: str
    status: str          # "ready" | "planned"
    class_name: str
    model: str
    requires: str
    dim: int | None = None  # embedding only


@dataclass
class LayerConfig:
    primary: str
    fallback: str | None
    available: dict[str, ProviderEntry]

    def primary_entry(self) -> ProviderEntry:
        return self.available[self.primary]

    def fallback_entry(self) -> ProviderEntry | None:
        if self.fallback:
            return self.available[self.fallback]
        return None


@dataclass
class ProviderConfig:
    embedding: LayerConfig
    llm: LayerConfig
    runtime: LayerConfig


def load_provider_config(path: str | Path | None = None) -> ProviderConfig:
    if path is None:
        path = _find_providers_yaml()
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return _parse(raw)


def _find_providers_yaml() -> Path:
    # Walk up from cwd until providers.yaml is found (works from notebook subdirs)
    current = Path(os.getcwd())
    for directory in [current, *current.parents]:
        candidate = directory / "providers.yaml"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("providers.yaml not found in any parent directory")


def _parse(raw: dict) -> ProviderConfig:
    return ProviderConfig(
        embedding=_parse_layer(raw["embedding"]),
        llm=_parse_layer(raw["llm"]),
        runtime=_parse_layer(raw["runtime"]),
    )


def _parse_layer(raw: dict) -> LayerConfig:
    available = {
        name: ProviderEntry(
            name=name,
            status=entry["status"],
            class_name=entry["class"],
            model=entry["model"],
            requires=entry["requires"],
            dim=entry.get("dim"),
        )
        for name, entry in raw["available"].items()
    }
    return LayerConfig(
        primary=raw["primary"],
        fallback=raw.get("fallback"),
        available=available,
    )
