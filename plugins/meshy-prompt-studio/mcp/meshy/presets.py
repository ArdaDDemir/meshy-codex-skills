"""Workflow presets for one-command asset pack creation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import MeshyError


@dataclass(frozen=True)
class WorkflowPreset:
    name: str
    preview_defaults: dict[str, Any] = field(default_factory=dict)
    refine_defaults: dict[str, Any] = field(default_factory=dict)
    target_formats: list[str] = field(default_factory=lambda: ["glb"])
    prompt_suffix: str = ""
    notes: list[str] = field(default_factory=list)


PRESETS: dict[str, WorkflowPreset] = {
    "game_prop": WorkflowPreset(
        name="game_prop",
        target_formats=["glb"],
        refine_defaults={"enable_pbr": True},
        prompt_suffix=(
            "Game-ready static prop with a clean silhouette, coherent proportions, production-friendly "
            "surface detail, and UV-friendly materials."
        ),
        notes=["Game prop preset: GLB output, refine on, PBR textures on, no pose mode."],
    ),
    "low_poly_asset": WorkflowPreset(
        name="low_poly_asset",
        preview_defaults={"model_type": "lowpoly"},
        target_formats=["glb"],
        refine_defaults={"enable_pbr": True},
        prompt_suffix=(
            "Low-poly game asset with readable forms, clean simplified shapes, efficient geometry, "
            "and crisp material separation."
        ),
        notes=["Low-poly preset: model_type=lowpoly, GLB output, refine on, PBR textures on."],
    ),
    "riggable_character": WorkflowPreset(
        name="riggable_character",
        preview_defaults={"pose_mode": "a-pose", "symmetry_mode": "on"},
        target_formats=["glb", "fbx"],
        refine_defaults={"enable_pbr": True},
        prompt_suffix=(
            "Rig-friendly humanoid character in a clean A-pose, arms separated from the torso, "
            "visible hands, symmetrical body, neutral expression, and deformation-friendly clothing."
        ),
        notes=[
            "Rig-friendly character preset: a-pose, GLB and FBX outputs where supported, refine on.",
            "Use a visual character prompt for appearance, but keep the body pose simple for rigging.",
        ],
    ),
    "printable_model": WorkflowPreset(
        name="printable_model",
        target_formats=["stl", "3mf"],
        refine_defaults={"enable_pbr": False},
        prompt_suffix=(
            "3D printable solid object, watertight form, stable base, no thin fragile parts, "
            "no floating pieces, and clear physical separations."
        ),
        notes=["Printable preset: STL and 3MF outputs, no rig assumptions, print-safe geometry hints."],
    ),
}


def normalize_preset_name(value: Any) -> str:
    name = str(value or "game_prop").strip().lower().replace("-", "_")
    if name not in PRESETS:
        allowed = ", ".join(sorted(PRESETS))
        raise MeshyError(f"Unsupported preset '{value}'. Supported presets: {allowed}.")
    return name


def get_preset(value: Any) -> WorkflowPreset:
    return PRESETS[normalize_preset_name(value)]


def enrich_prompt(prompt: str, preset: WorkflowPreset) -> str:
    prompt = prompt.strip()
    if not preset.prompt_suffix:
        return prompt
    return f"{prompt}. {preset.prompt_suffix}"
