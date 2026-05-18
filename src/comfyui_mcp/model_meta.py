"""describe_model helpers — safetensors header reading, .pth/.pt inspection, model
classification, and type-aware summary building."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# Kind classification: by category subdir first, then heuristic from filename + suffix
_LORA_CATEGORIES = {"loras", "lycoris"}
_CHECKPOINT_CATEGORIES = {"checkpoints", "diffusion_models", "diffusers"}
_UPSCALER_CATEGORIES = {"upscale_models"}
_CONTROLNET_CATEGORIES = {"controlnet"}
_VAE_CATEGORIES = {"vae", "vae_approx"}
_CLIP_CATEGORIES = {"text_encoders", "clip", "clip_vision"}

# Noisy safetensors metadata keys we drop — useful distillations end up in summary anyway
_NOISY_META_KEYS = {
    "ss_tag_frequency", "ss_dataset_dirs", "ss_datasets", "ss_bucket_info",
    "ss_session_id", "ss_training_started_at", "ss_training_finished_at",
    "ss_sd_scripts_commit_hash", "ss_steps", "ss_epoch",
    "ss_training_comment", "ss_full_fp16", "ss_seed", "ss_v2",
    "ss_face_crop_aug_range", "ss_random_crop", "ss_keep_tokens",
    "ss_max_grad_norm", "ss_max_token_length", "ss_min_snr_gamma",
    "ss_caption_dropout_rate", "ss_caption_dropout_every_n_epochs",
    "ss_caption_tag_dropout_rate", "ss_color_aug", "ss_flip_aug",
    "ss_gradient_accumulation_steps", "ss_gradient_checkpointing",
    "ss_huber_c", "ss_huber_schedule", "ss_loss_type",
    "ss_lr_scheduler", "ss_lr_warmup_steps", "ss_max_train_steps",
    "ss_mixed_precision", "ss_multires_noise_discount",
    "ss_multires_noise_iterations", "ss_network_alpha",
    "ss_network_args", "ss_network_dropout", "ss_network_module",
    "ss_new_sd_model_hash", "ss_noise_offset", "ss_noise_offset_random_strength",
    "ss_num_batches_per_epoch", "ss_num_epochs", "ss_num_reg_images",
    "ss_num_train_images", "ss_optimizer", "ss_prior_loss_weight",
    "ss_resolution", "ss_scale_weight_norms", "ss_sd_model_hash",
    "ss_text_encoder_lr", "ss_unet_lr", "ss_zero_terminal_snr",
    "ss_ip_noise_gamma", "ss_ip_noise_gamma_random_strength",
    "ss_debiased_estimation", "ss_lowram", "ss_clip_skip",
    "ss_cache_latents", "ss_adaptive_noise_scale",
    "sshs_model_hash", "sshs_legacy_hash",
    "ss_sd_model_name",  # often huge path strings
}


def _classify_model(path: Path, category: str) -> str:
    """Classify model kind from category + filename + suffix."""
    cat = (category or "").lower()
    if cat in _LORA_CATEGORIES or "lora" in path.parts or "lora" in path.stem.lower():
        return "lora"
    if cat in _CHECKPOINT_CATEGORIES:
        return "checkpoint"
    if cat in _UPSCALER_CATEGORIES or path.suffix.lower() in (".pth", ".pt"):
        # .pth/.pt typically upscalers; safetensors in upscale_models also valid
        return "upscaler"
    if cat in _CONTROLNET_CATEGORIES:
        return "controlnet"
    if cat in _VAE_CATEGORIES:
        return "vae"
    if cat in _CLIP_CATEGORIES:
        return "text_encoder"
    # Heuristic fallback: try to infer from path components
    parts_lower = {p.lower() for p in path.parts}
    if parts_lower & _LORA_CATEGORIES:
        return "lora"
    if parts_lower & _CHECKPOINT_CATEGORIES:
        return "checkpoint"
    if parts_lower & _UPSCALER_CATEGORIES:
        return "upscaler"
    if parts_lower & _CONTROLNET_CATEGORIES:
        return "controlnet"
    return "other"


def _trim_safetensors_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Drop noisy raw fields from kohya-style safetensors metadata. The useful bits
    (top tags, trigger phrase, architecture) are extracted into `summary` separately."""
    return {k: v for k, v in meta.items() if k not in _NOISY_META_KEYS}


def _model_summary(kind: str, meta: dict[str, Any], sf: dict[str, Any] | None) -> dict[str, Any]:
    """Build the type-aware, structured summary the agent actually needs."""
    summary: dict[str, Any] = {
        "kind": kind,
        "title": meta.get("modelspec.title"),
        "description": (meta.get("modelspec.description") or "")[:500] or None,
        "architecture": meta.get("modelspec.architecture") or meta.get("ss_base_model_version"),
    }
    if kind == "lora":
        summary["trigger_phrase"] = meta.get("modelspec.trigger_phrase")
        summary["output_name"] = meta.get("ss_output_name")
        summary["training_top_tags"] = _top_training_tags(meta, limit=15)
        summary["recommended_strength_range"] = "0.4-0.7 (typical)"
    elif kind == "checkpoint":
        summary["embedded_vae"] = meta.get("modelspec.has_vae")
        summary["sai_resolution"] = meta.get("modelspec.resolution")
    elif kind == "controlnet":
        summary["controlnet_type"] = meta.get("modelspec.implementation") or "(check filename for hint: depth/canny/openpose/tile/...)"
    return {k: v for k, v in summary.items() if v is not None}


def _top_training_tags(meta: dict[str, Any], limit: int = 15) -> list[str]:
    """Extract the most-frequent training tags from kohya's ss_tag_frequency JSON."""
    tags = meta.get("ss_tag_frequency")
    if not isinstance(tags, str):
        return []
    try:
        tag_dict = json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        return []
    flat: dict[str, int] = {}
    for _ds, counts in tag_dict.items():
        if isinstance(counts, dict):
            for tag, count in counts.items():
                flat[tag] = flat.get(tag, 0) + (count if isinstance(count, int) else 1)
    return [t for t, _ in sorted(flat.items(), key=lambda x: -x[1])[:limit]]


def _inspect_pytorch_state(path: Path) -> dict[str, Any]:
    """Read a .pth/.pt PyTorch state dict safely (weights_only=True). Returns key stats
    the agent can reason about without loading the full model: tensor count, common
    shape patterns, key prefixes (which hint at architecture)."""
    try:
        import torch  # type: ignore[import-untyped]
    except ImportError:
        return {"error": "torch not available; install for .pth inspection"}
    try:
        # weights_only=True since 2.4 — safely reject pickled callables
        state = torch.load(str(path), map_location="cpu", weights_only=True)
    except Exception as e:
        return {"error": f"torch.load failed: {e}"}

    if isinstance(state, dict) and not all(hasattr(v, "shape") for v in state.values()):
        # nested format — drill in if a 'model'/'state_dict' wrapper is present
        for key in ("model", "state_dict", "params"):
            if key in state and isinstance(state[key], dict):
                state = state[key]
                break

    if not isinstance(state, dict):
        return {"error": f"unexpected state type: {type(state).__name__}"}

    keys = list(state.keys())
    # Common architecture key prefixes
    key_prefixes: dict[str, int] = {}
    for k in keys:
        prefix = str(k).split(".", 1)[0]
        key_prefixes[prefix] = key_prefixes.get(prefix, 0) + 1
    top_prefixes = sorted(key_prefixes.items(), key=lambda x: -x[1])[:5]
    return {
        "tensor_count": len(keys),
        "top_key_prefixes": [{"prefix": p, "count": c} for p, c in top_prefixes],
        "first_keys": keys[:5],
    }


def _upscaler_summary_from_state(info: dict[str, Any]) -> dict[str, Any]:
    """Infer scale factor + architecture flavor from a torch state dict's key shapes.
    Best-effort — covers the common ESRGAN / Real-ESRGAN / SwinIR / SRVGGNet patterns."""
    if "error" in info:
        return {"error": info["error"]}
    prefixes = {p["prefix"]: p["count"] for p in info.get("top_key_prefixes", [])}
    summary: dict[str, Any] = {"kind": "upscaler", "tensor_count": info.get("tensor_count")}
    if "RRDB_trunk" in prefixes or "RRDB" in str(info.get("first_keys", [])):
        summary["architecture"] = "ESRGAN (RRDB trunk)"
    elif "body" in prefixes and "conv_first" in prefixes:
        summary["architecture"] = "Real-ESRGAN / SRResNet variant"
    elif "layers" in prefixes:
        summary["architecture"] = "SwinIR (transformer)"
    elif "head" in prefixes and "body" in prefixes:
        summary["architecture"] = "SRVGGNet (Real-ESRGAN compact)"
    else:
        summary["architecture"] = "unknown (inspect first_keys for clues)"
    summary["note"] = "scale factor not auto-detected; check filename (e.g. '4x-AnimeSharp' = 4x)"
    return summary


def _read_safetensors_metadata(path: Path) -> dict[str, Any]:
    """Read the JSON header from a .safetensors file. Cheap (reads at most ~100MB,
    typically <2MB), and fails fast on truncation/corruption — exactly what catches
    incomplete downloads before they hit a runtime crash."""
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            head = f.read(8)
            if len(head) < 8:
                return {"error": "file too short to contain a header"}
            header_len = int.from_bytes(head, "little")
            if header_len <= 0:
                return {"error": f"non-positive header length {header_len}"}
            if header_len > 100_000_000:
                return {"error": f"absurd header length {header_len} (file likely not safetensors)"}
            if 8 + header_len > size:
                return {
                    "error": "header truncated — file is incomplete (partial download?)",
                    "expected_at_least_bytes": 8 + header_len,
                    "actual_bytes": size,
                }
            body = f.read(header_len)
            if len(body) < header_len:
                return {"error": "could not read full header"}
        try:
            hdr = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            return {"error": f"invalid JSON header: {e}"}
        except UnicodeDecodeError as e:
            return {"error": f"header is not UTF-8: {e}"}
        meta = hdr.get("__metadata__") or {}
        tensor_count = sum(1 for k in hdr if k != "__metadata__")

        # Check tensor data isn't truncated. Header lists each tensor's data_offsets
        # [start, end] relative to the start of the data block (which begins at
        # byte 8 + header_len). If the highest 'end' exceeds the file's actual
        # remaining bytes, the safetensors is corrupted — even if the header
        # itself parses cleanly. This is the "file not fully covered" case.
        max_end = 0
        for k, v in hdr.items():
            if k == "__metadata__" or not isinstance(v, dict):
                continue
            offsets = v.get("data_offsets")
            if isinstance(offsets, list) and len(offsets) >= 2 and isinstance(offsets[1], int):
                if offsets[1] > max_end:
                    max_end = offsets[1]
        expected_total = 8 + header_len + max_end
        if expected_total > size:
            return {
                "error": "tensor data truncated — file is incomplete (partial download?)",
                "expected_bytes": expected_total,
                "actual_bytes": size,
                "shortfall_bytes": expected_total - size,
                "metadata": meta,
                "tensor_count": tensor_count,
            }

        return {
            "metadata": meta,
            "tensor_count": tensor_count,
            "header_bytes": header_len,
            "tensor_data_bytes": max_end,
        }
    except OSError as e:
        return {"error": str(e)}
