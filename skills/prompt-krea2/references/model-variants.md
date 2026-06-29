# Krea 2 — Variants, Settings, and Encoder Notes

Krea 2 is a 12B open-weights text-to-image model from Krea, distributed by Comfy-Org on HuggingFace and run locally in ComfyUI. It uses a **Qwen3-VL** text encoder (a vision-language model, which is why it has strong multilingual handling and accepts image-based style references). It placed 2nd among independent-lab models on public leaderboards per Krea's technical report.

Settings below are the community/official consensus as of mid-2026. They diverge in a couple of places (noted); when in doubt, the workflow's own defaults are the safest starting point, and the user's installed ComfyUI version is the real source of truth.

## The two open-weights variants

| Variant | Steps | CFG | Sampler / scheduler | Use case |
|---|---|---|---|---|
| **Krea 2 Turbo** | 8 | 0–1 (effectively off) | `er_sde` / `simple` (official-leaning); `euler` or `euler_ancestral` / `simple` or `normal` (hands-on guides) | Fast distilled checkpoint. The default for almost everyone. ~2s at 2K on strong consumer GPUs. |
| **Krea 2 Raw** (Base) | 52 | ~3.5 | full-step sampling | Base model, diverse, ideal for fine-tuning and LoRA training. Slower, higher ceiling. Takes a real negative prompt (CFG > 1). |

- **Resolution:** 1024–2048px native. Set megapixels to 2.0 for 2K. Turbo targets native 2K.
- **Steps on Turbo:** going above 8 gives little benefit — it's distilled for low-step inference.
- **Negative prompt:** Turbo at CFG 1 ignores it (don't write one; describe positive opposites). Raw at CFG ~3.5 can use one.

> Naming trap: Krea's **hosted API** tiers are called **Krea 2 Medium** (best at illustration/anime/painting) and **Krea 2 Large** (best at photoreal/raw aesthetics). Those are a *different product* from the open-weights **Raw/Turbo** you run in ComfyUI. Don't map "Medium = anime, Large = photo" onto Turbo/Raw — Turbo does both.

## Quant builds

The open weights ship in several quantizations. Pick by VRAM:

| Build | Size (Turbo) | Notes |
|---|---|---|
| BF16 | ~24.76 GiB | Full precision; needs a big card. |
| **FP8 (scaled)** | ~12.01 GiB | The right default for most people; runs on 16–24 GB GPUs. This is what the standard ComfyUI template loads (`krea2_turbo_fp8_scaled.safetensors`). |
| NVFP4 / INT8 | smaller | Newer low-bit builds; quality/speed tradeoff. |
| GGUF | varies by quant level | Community GGUF workflows let you trade quality for VRAM/speed; pick the quant level for your card. |

Companion files in the standard workflow: text encoder `qwen3vl_4b_fp8_scaled.safetensors`, VAE `qwen_image_vae.safetensors`.

## The built-in prompt enhancer

The ComfyUI workflow includes an LLM-powered prompt expander (a `TextGenerate` node, or a local Gemma/Qwen stand-in) controlled by a `prompt_enhance` toggle, with an `LLM_max_token` length control. It exists because Krea was trained on dense captions but users type short prompts — the expander bridges that gap.

**Because this skill produces the dense caption itself, turn the enhancer OFF when feeding it skill output** — otherwise you double-enhance and lose control. Disconnect the node or set `prompt_enhance` / "Refine Prompt?" to `false`.

Known quirk reported in the wild: some early versions of the enhancer's system prompt leaked the LLM's "thinking" into the prompt body. If the user's enhancer output looks like it contains reasoning text, that's the bug — bypass the enhancer and feed a finished prompt instead.

## Abliterated Qwen3-VL encoder (community option)

Some community workflows swap the stock text encoder for an **abliterated Qwen3-VL** build — one with some safety alignment removed — to interpret prompts "more literally," preserve complex prompts the aligned encoder rewrites, and handle artistic/fictional/mature themes. The official release doesn't require it. Mention it only if the user reports the model ignoring or rewriting parts of their prompt; it's an install-level swap, not something the prompt text controls.

## Style reference system

Beyond text, Krea 2 supports **image-based style references** (its Qwen3-VL encoder accepts images). Each reference image gets a strength (0–100%); multiple references blend. Community guidance: start weights around 0.6–0.75, push higher on the image doing more of the aesthetic work. This is separate from the style LoRAs — use it when words can't capture a look the user can show.

## Style LoRAs

Trigger convention is uniform: a short **"<descriptor> style"** phrase at strength **0.8–1.0**. The set in the HF `Comfy-Org/Krea-2/loras` repo grows over time and differs between installs, so **don't hardcode the list** — read each LoRA's real trigger from its safetensors metadata via the MCP's `suggest_local_loras(intent, base_model="krea")` or `/find-loras`. Observed examples: `krea2_darkbrush` → "monochrome ink wash style", `krea2_retroanime` → "purple retro anime style", `krea2_softwatercolor` → "art deco watercolor style". Note the workflow's CustomCombo node may append the trigger word automatically — check before appending it yourself, to avoid doubling.
