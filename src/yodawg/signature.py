import os
from datetime import datetime
from typing import Optional


def _bool_env(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _pick_model_emoji(model: Optional[str]) -> str:
    if not model:
        return "🤖"
    m = model.lower()
    
    if "llama" in m:
        return "🦙"
    if "gpt" in m:
        return "🧠"
    if "claude" in m:
        return "🤖"
    if "gemma" in m:
        return "✨"
    return "🤖"


def _now_strings():
    now = datetime.utcnow()
    return {
        "timestamp": now.isoformat(timespec="seconds") + "Z",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S") + "Z",
    }


def build_signature(mode: Optional[str] = None, model: Optional[str] = None) -> str:
    """
    Build a customizable signature for appended comments/captions.

    Environment variables:
    - SIGNATURE_ENABLED: bool (default: true)
    - SIGNATURE_TEMPLATE: custom template with placeholders below
    - SIGNATURE_STYLE: classic|minimal|emoji (default: classic) — used if template not set
    - SIGNATURE_BRAND: e.g. "Yo Dawg Action Server" (default)
    - SIGNATURE_URL: optional URL to include (repo, product, docs)
    - SIGNATURE_PREFIX_NEWLINE: bool (default: true) — prepend a leading newline
    - SIGNATURE_HASHTAGS: optional like "#YoDawg #MCP"
    - SIGNATURE_MAX_LENGTH: int, trim if exceeded (default: 280)
    - SIGNATURE_INCLUDE_SEMA4: bool (default: true) — ensure 'Sema4.ai' is present
    - SIGNATURE_SEMA4_LABEL: string (default: 'Sema4.ai') — customize label text

    Placeholders available in SIGNATURE_TEMPLATE:
    {mode} {model} {brand} {url} {timestamp} {date} {time} {emoji_brand} {emoji_model} {hashtags}
    """
    if not _bool_env("SIGNATURE_ENABLED", True):
        return ""

    style = (os.getenv("SIGNATURE_STYLE") or "classic").strip().lower()
    brand = os.getenv("SIGNATURE_BRAND") or "Yo Dawg Action Server"
    url = os.getenv("SIGNATURE_URL") or ""
    hashtags = os.getenv("SIGNATURE_HASHTAGS") or ""
    prefix_nl = _bool_env("SIGNATURE_PREFIX_NEWLINE", True)
    max_len = int(os.getenv("SIGNATURE_MAX_LENGTH") or 280)
    #include_sema4 = _bool_env("SIGNATURE_INCLUDE_SEMA4", True)
    #sema4_label = os.getenv("SIGNATURE_SEMA4_LABEL")

    emoji_brand = "🐶"
    #model = model.split("ollama:", 1)[1].strip()
    emoji_model = _pick_model_emoji(model)

    # Default templates per style (used only if SIGNATURE_TEMPLATE not set)
    if style == "minimal":
        default_tpl = "— {brand} • {mode} • {model}"
    elif style == "emoji":
        default_tpl = "{emoji_brand} {brand} • {emoji_model} {model} • {mode}"
    else:  # classic
        default_tpl = "— {emoji_brand} {brand} | Sema4.ai • MCP | model: {model}"

    tpl = os.getenv("SIGNATURE_TEMPLATE") or default_tpl

    # Build context
    ctx = {
        **_now_strings(),
        "mode": (mode or "unknown"),
        "model": (model or "unknown"),
        "brand": brand,
        "url": url,
        "emoji_brand": emoji_brand,
        "emoji_model": emoji_model,
        "hashtags": hashtags.strip(),
    }

    try:
        core = tpl.format(**ctx).strip()
    except Exception:
        # Fall back to a safe default if formatting fails
        core = f"— {brand} • mode: {ctx['mode']} • model: {ctx['model']}"

    parts = [core]
    # Ensure Sema4.ai is present at least once if requested
    
    if url:
        parts.append(url.strip())
    if hashtags:
        parts.append(hashtags.strip())

    sig = " | ".join(parts)
    if prefix_nl:
        sig = "\n" + sig

    if len(sig) > max_len:
        sig = sig[: max(0, max_len - 1)] + "…"

    return sig
