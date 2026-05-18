"""Tab access + queue submission helpers — the bridge between live ComfyUI tabs
and the offline queue API. Used by every tool that runs/queries the open workflow."""
from __future__ import annotations

from typing import Any

from .client import comfy


async def _workflow_from_tab(
    tab_id: str = "", want_api: bool = False
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Pull workflow from the bridge for a tab. Returns (workflow, state, error_response).
    Exactly one of workflow/error_response is non-None on success/failure."""
    state = await comfy.bridge_state(tab_id=tab_id or None)
    if state.get("error"):
        return None, state, state
    wf = state.get("api_workflow" if want_api else "workflow")
    if wf is None:
        fmt_label = "api-format" if want_api else "ui-format"
        return None, state, {
            "error": f"no {fmt_label} workflow available",
            "hint": "is the bridge installed and a browser tab open with a valid graph?",
            "tab_count": state.get("tab_count", 0),
        }
    return wf, state, None


async def _queue_and_enrich(
    workflow: dict[str, Any], client_id: str | None = None
) -> dict[str, Any]:
    """Submit a workflow and shape the response uniformly: {ok, prompt_id?, error?, node_errors?}.
    On validation failure, node_errors are enriched with valid_values from /object_info."""
    status, body = await comfy.queue(workflow, client_id=client_id)
    if status == 200:
        return {"ok": True, **body}
    if "node_errors" in body:
        body = {**body, "node_errors": await _enrich_node_errors(body["node_errors"] or {}, workflow)}
    return {"ok": False, **body}


async def _enrich_node_errors(
    node_errors: dict[str, Any], workflow: dict[str, Any]
) -> dict[str, Any]:
    """Backfill `valid_values` on value_not_in_list errors where ComfyUI returned a null
    input_config (happens for dynamically-populated combos like model lists)."""
    if not node_errors:
        return node_errors
    out: dict[str, Any] = {}
    for node_id, info in node_errors.items():
        info_copy = dict(info)
        errs_out: list[dict[str, Any]] = []
        for err in info.get("errors", []) or []:
            err_copy = dict(err)
            if err.get("type") == "value_not_in_list":
                extra = err.get("extra_info") or {}
                input_name = extra.get("input_name")
                input_config = extra.get("input_config")
                already_have_list = (
                    isinstance(input_config, list)
                    and input_config
                    and isinstance(input_config[0], list)
                )
                if input_name and not already_have_list:
                    class_type = info.get("class_type") or (
                        workflow.get(node_id, {}).get("class_type")
                        if isinstance(node_id, str)
                        else None
                    )
                    if class_type:
                        try:
                            oi = await comfy.object_info(class_type)
                            spec = (oi.get(class_type, {}) or {}).get("input", {}) or {}
                            for section in ("required", "optional"):
                                decl = (spec.get(section) or {}).get(input_name)
                                if decl:
                                    t = (
                                        decl[0]
                                        if isinstance(decl, (list, tuple)) and decl
                                        else None
                                    )
                                    if isinstance(t, list):
                                        err_copy["valid_values"] = t
                                    break
                        except Exception:
                            pass
            errs_out.append(err_copy)
        info_copy["errors"] = errs_out
        out[node_id] = info_copy
    return out
