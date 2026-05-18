"""Log-parsing helpers — noise filters, traceback extraction, history scrubbing."""
from __future__ import annotations

import re
from typing import Any


# Noise patterns: HF/transformers weight printouts, common progress bars, and lines
# that are pure metadata. Compiled once at module import.
_NOISE_PATTERNS = [
    # HuggingFace transformers weight enumeration: ".language_model.layers.0.mlp.weight"
    re.compile(r"^\s*(model\.)?(language_model|vision_model|text_encoder|encoder|decoder|transformer)\..*\.(weight|bias|gamma|beta|running_mean|running_var)\s*$"),
    re.compile(r"^\s*[\w.]+\.layers\.\d+\..*\.(weight|bias)\s*$"),
    # tqdm-style progress bars (Unicode-block AND ASCII-hash variants)
    re.compile(r"^\s*\d+%\|[█▌▏#=\- ]*\|\s*\d+/\d+"),
    re.compile(r"^\s*\d+it \[\d+:\d+, "),
    # ComfyUI per-token sampler progress (a single line that gets cleared via \r in TTYs but
    # ends up as separate lines in file logs)
    re.compile(r"^\s*\d+%\|.* it/s\]"),
]


def _is_log_noise(line: str) -> bool:
    return any(p.match(line) for p in _NOISE_PATTERNS)


def _strip_history_warnings(history: dict[str, Any]) -> dict[str, Any]:
    """Drop noise lines from history.status.messages. ComfyUI structures these as
    [event_type, payload_dict] pairs; messages of type 'logs' or with a nested 'entries'
    list are the heaviest. Mutates a shallow copy."""
    status = history.get("status")
    if not isinstance(status, dict):
        return history
    messages = status.get("messages")
    if not isinstance(messages, list):
        return history

    cleaned: list[Any] = []
    for msg in messages:
        if not isinstance(msg, list) or len(msg) < 2:
            cleaned.append(msg)
            continue
        ev_type, payload = msg[0], msg[1]
        if isinstance(payload, dict) and isinstance(payload.get("entries"), list):
            kept = [e for e in payload["entries"]
                    if not isinstance(e, str) or not _is_log_noise(e)]
            if kept:
                cleaned.append([ev_type, {**payload, "entries": kept}])
            continue
        if isinstance(payload, dict) and isinstance(payload.get("message"), str):
            if _is_log_noise(payload["message"]):
                continue
        cleaned.append(msg)

    return {**history, "status": {**status, "messages": cleaned}}


def _extract_traceback_blocks(all_lines: list[str], limit: int) -> list[dict[str, Any]]:
    """Extract the last `limit` traceback blocks from log lines.

    A block runs from a 'Traceback (most recent call last):' marker through the
    last indented frame and the final exception line (typically un-indented and
    starting with the exception class name + ':').
    """
    blocks: list[dict[str, Any]] = []
    i = 0
    n = len(all_lines)
    while i < n:
        if "Traceback (most recent call last):" in all_lines[i]:
            start = i
            j = i + 1
            # Walk forward over indented frame lines + a trailing un-indented exception line.
            # Stop when we hit a line that's neither indented nor matches the exception pattern.
            exception_line_idx = None
            while j < n:
                ln = all_lines[j]
                if ln.startswith((" ", "\t")):
                    j += 1
                    continue
                # Un-indented line: the exception terminator if it looks like "Foo: msg"
                if exception_line_idx is None and re.match(r"^[A-Z][\w.]*(Error|Exception|Warning|Interrupt|Failed|NotImplemented)[\w.]*: ", ln):
                    exception_line_idx = j
                    j += 1
                    break
                if exception_line_idx is None and re.match(r"^[\w.]+: \S", ln):
                    exception_line_idx = j
                    j += 1
                    break
                # End of block without classic terminator
                break
            end = j
            preceding = all_lines[max(0, start - 1)] if start > 0 else ""
            blocks.append({
                "start_line": start,
                "preceding_line": preceding[-300:],
                "lines": all_lines[start:end],
                "exception": all_lines[exception_line_idx][:500] if exception_line_idx is not None else None,
            })
            i = end
            continue
        i += 1
    return blocks[-limit:] if limit > 0 else blocks


def _traceback_block_above(lines: list[str], idx: int, max_lookback: int = 200) -> list[str] | None:
    """Walk backward from idx looking for the most recent 'Traceback (most recent call last):'
    marker, then return that block (forward-walked from there). None if not found nearby."""
    start_search = max(0, idx - max_lookback)
    for j in range(idx - 1, start_search - 1, -1):
        if "Traceback (most recent call last):" in lines[j]:
            return _walk_traceback(lines, j)
    return None


def _traceback_block_below(lines: list[str], idx: int, max_lookahead: int = 200) -> list[str] | None:
    """Walk forward from idx looking for the next 'Traceback (most recent call last):' marker."""
    end = min(len(lines), idx + max_lookahead)
    for j in range(idx + 1, end):
        if "Traceback (most recent call last):" in lines[j]:
            return _walk_traceback(lines, j)
    return None


def _walk_traceback(lines: list[str], start: int) -> list[str]:
    """Forward-walk an intact traceback block starting at `start`. Includes the
    Traceback marker, indented frames, and the final exception-class line if present."""
    if start >= len(lines):
        return []
    out = [lines[start]]
    j = start + 1
    while j < len(lines):
        ln = lines[j]
        if ln.startswith((" ", "\t")):
            out.append(ln)
            j += 1
            continue
        # Un-indented terminator: classic "ClassName: message" or "ClassName"
        if re.match(r"^[A-Z][\w.]*(Error|Exception|Warning|Interrupt|Failed|NotImplemented)[\w.]*(:\s|$)", ln):
            out.append(ln)
            break
        if re.match(r"^[\w.]+: \S", ln):
            out.append(ln)
            break
        break
    return out
