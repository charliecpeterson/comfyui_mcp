"""Widget-name / positional-index alignment for UI-format workflows.

ComfyUI's UI saves `widgets_values` as a positional list. To edit by name, we need
to map name → index using `/object_info`, while accounting for the frontend-injected
`*_control_after_generate` synthetic widget that follows any widget with
`control_after_generate: True` (most commonly `seed` on KSampler).
"""
from __future__ import annotations

from typing import Any

from .client import comfy


_WIDGET_TYPES = {"STRING", "INT", "FLOAT", "BOOLEAN"}


async def _ui_widget_order(class_type: str) -> list[str]:
    """Map widget input names to their positional index in widgets_values for a node class.

    Critical: accounts for synthetic *_control_after_generate widgets that ComfyUI's
    frontend injects right after any widget with `control_after_generate: True` in its
    options (most commonly `seed` on KSampler). Without this, the position-to-name
    mapping silently shifts after the seed and corrupts edits/reads from that point on.
    """
    info = await comfy.object_info(class_type)
    spec = info.get(class_type, {}).get("input", {})
    order: list[str] = []
    for section in ("required", "optional"):
        for name, decl in (spec.get(section) or {}).items():
            t = decl[0] if isinstance(decl, (list, tuple)) and decl else decl
            opts = decl[1] if isinstance(decl, (list, tuple)) and len(decl) > 1 else {}
            opts = opts if isinstance(opts, dict) else {}
            is_widget = False
            if isinstance(t, list):
                if not opts.get("forceInput"):
                    order.append(name)  # COMBO[...]
                    is_widget = True
            elif isinstance(t, str) and t in _WIDGET_TYPES:
                if not opts.get("forceInput"):
                    order.append(name)
                    is_widget = True
            # Frontend-injected control widget for INT seed-style inputs
            if is_widget and opts.get("control_after_generate"):
                order.append(f"{name}_control_after_generate")
    return order


async def _ui_widget_order_aligned(class_type: str, actual_len: int) -> tuple[list[str], str]:
    """Pick the widget-name order that matches the actual widgets_values length.

    Different ComfyUI nodes follow different conventions for the seed_control_after_generate
    synthetic widget — most stock nodes have it, but custom nodes (Impact Pack's FaceDetailer,
    UltimateSDUpscale, etc.) often don't, even when their seed widget declares
    control_after_generate: True. Trying both variants and picking the matching length is
    the only robust resolution without per-node hardcoding.

    Returns (order, confidence) where confidence ∈ {"with_control", "without_control",
    "best_guess"} — agents/UI can surface "best_guess" cases as a warning.
    """
    with_control = await _ui_widget_order(class_type)
    if len(with_control) == actual_len:
        return with_control, "with_control"
    without_control = [n for n in with_control if not n.endswith("_control_after_generate")]
    if len(without_control) == actual_len:
        return without_control, "without_control"
    # Neither matches — return whichever is closer in length, with low confidence
    diff_with = abs(len(with_control) - actual_len)
    diff_without = abs(len(without_control) - actual_len)
    return (with_control if diff_with <= diff_without else without_control), "best_guess"


def _flatten_inputs(spec: dict[str, Any]) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for section in ("required", "optional"):
        for n, v in (spec.get(section) or {}).items():
            out.append((n, v[0] if isinstance(v, (list, tuple)) and v else v))
    return out


def _socket_type(t: Any) -> str:
    if isinstance(t, str):
        return t.upper()
    if isinstance(t, list):
        return "ENUM"
    return str(t).upper()
