import io
import json
import urllib.error

import outrun_ai
import pytest
from outrun_ai import OutrunError, _prices, prices

FEED = {
    "currency": "USD",
    "generated_at": 1,
    "paused": ["paused-model"],
    "models": [
        {"id": "text-a", "name": "Text A", "family": "f", "kind": "text", "unit": "1M tokens",
         "tiers": [{"label": "all", "unit": "1M tokens", "prices": {"input": 0.1, "output": 0.4}}]},
        {"id": "img-b", "name": "Image B", "family": "image", "kind": "image", "unit": "image",
         "tiers": [{"label": "all", "unit": "image", "prices": {"output": 0.02}}]},
        {"id": "paused-model", "name": "Paused", "family": "f", "kind": "text", "unit": "1M tokens",
         "tiers": []},
    ],
}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def seen(monkeypatch):
    """Replace urlopen so no test touches the network; record each request."""
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append((req, timeout))
        return FakeResponse(json.dumps(FEED).encode())

    monkeypatch.setattr(_prices.urllib.request, "urlopen", fake_urlopen)
    return calls


def test_exported():
    assert outrun_ai.prices is prices
    assert outrun_ai.PRICING_URL == "https://api.outrun.to/pricing"


def test_returns_active_models_with_paused_flag(seen):
    out = prices()
    assert [m["id"] for m in out] == ["text-a", "img-b"]
    assert all(m["paused"] is False for m in out)
    assert out[0]["tiers"][0]["prices"]["output"] == 0.4


def test_kind_filter_and_include_paused(seen):
    assert [m["id"] for m in prices("text")] == ["text-a"]
    both = prices(kind="text", include_paused=True)
    assert [(m["id"], m["paused"]) for m in both] == [("text-a", False), ("paused-model", True)]


def test_request_url_user_agent_and_timeout(seen):
    prices(timeout=3)
    req, timeout = seen[0]
    assert req.full_url == "https://api.outrun.to/pricing"
    assert timeout == 3
    ua = req.get_header("User-agent")
    assert ua.startswith("Mozilla/5.0") and "outrun-ai-python/" in ua
    assert "Python-urllib" not in ua


def test_does_not_mutate_or_need_a_key(seen, monkeypatch):
    monkeypatch.delenv("OUTRUN_API_KEY", raising=False)
    prices()
    req, _ = seen[0]
    assert req.get_header("Authorization") is None
    assert "paused" not in FEED["models"][0]


def test_network_error_becomes_outrun_error(monkeypatch):
    def boom(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)

    monkeypatch.setattr(_prices.urllib.request, "urlopen", boom)
    with pytest.raises(OutrunError, match="price list"):
        prices()


def test_bad_format_becomes_outrun_error(monkeypatch):
    monkeypatch.setattr(
        _prices.urllib.request, "urlopen",
        lambda req, timeout=None: FakeResponse(b'{"unexpected": true}'),
    )
    with pytest.raises(OutrunError, match="format"):
        prices()
