from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, List, Optional

from ._client import OutrunError, __version__

PRICING_URL = "https://api.outrun.to/pricing"
# The feed's firewall blocks the default "Python-urllib" agent, so send our own.
_USER_AGENT = f"Mozilla/5.0 (compatible; outrun-ai-python/{__version__}; +https://outrun.to)"


def _fetch(url: str, timeout: float) -> Dict[str, Any]:
    req = urllib.request.Request(
        url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https URL)
        return json.loads(resp.read().decode("utf-8"))


def prices(
    kind: Optional[str] = None,
    *,
    include_paused: bool = False,
    timeout: float = 15.0,
    url: str = PRICING_URL,
) -> List[Dict[str, Any]]:
    """Return the public Outrun price list. No API key is needed and nothing is billed.

    Each item is a dict with ``id`` (the model name to send), ``name``, ``family``,
    ``kind`` (``"text"``, ``"image"``, ``"video"`` or ``"audio"``), ``unit`` and
    ``tiers`` (a list of ``{"label", "unit", "prices": {"input", "output", ...}}``,
    prices in USD per ``unit``), plus ``paused`` (bool).

    Args:
        kind: Only return models of this kind, for example ``"text"``.
        include_paused: Also return models that are paused right now.
        timeout: Seconds to wait for the feed.
        url: Feed URL. Only change this for testing.
    """
    try:
        feed = _fetch(url, timeout)
    except Exception as exc:  # network, HTTP or JSON errors
        raise OutrunError(f"Could not read the Outrun price list from {url}: {exc}") from exc
    if not isinstance(feed, dict) or not isinstance(feed.get("models"), list):
        raise OutrunError(f"Unexpected price list format from {url}")

    paused = set(feed.get("paused") or [])
    out = []
    for model in feed["models"]:
        if not isinstance(model, dict) or "id" not in model:
            continue
        item = dict(model)
        item["paused"] = item["id"] in paused
        if item["paused"] and not include_paused:
            continue
        if kind is not None and item.get("kind") != kind:
            continue
        out.append(item)
    return out
