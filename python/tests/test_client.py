import json

try:
    import httpx2 as httpx  # openai 3.x
except ImportError:  # openai 1.x / 2.x
    import httpx
import pytest
from outrun_ai import AsyncOutrun, Outrun, OutrunError

COMPLETION = {
    "id": "c1", "object": "chat.completion", "created": 1, "model": "m",
    "choices": [{"index": 0, "finish_reason": "stop",
                 "message": {"role": "assistant", "content": "hello there"}}],
}
SSE = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"role":"assistant","content":"Hel"}}]}\n\n'
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"lo"}}]}\n\n'
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
    "data: [DONE]\n\n"
)


def make_handler(seen):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = json.loads(request.content or b"{}")
        if body.get("stream"):
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=SSE)
        return httpx.Response(200, json=COMPLETION)
    return handler


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("OUTRUN_API_KEY", raising=False)


def client(seen, **kw):
    kw.setdefault("api_key", "test-key")
    return Outrun(http_client=httpx.Client(transport=httpx.MockTransport(make_handler(seen))), **kw)


def test_default_base_url():
    assert str(Outrun(api_key="k").base_url) == "https://api.outrun.to/v1/"


def test_custom_base_url():
    assert str(Outrun(api_key="k", base_url="http://localhost:1/v1").base_url) == "http://localhost:1/v1/"


def test_env_key(monkeypatch):
    monkeypatch.setenv("OUTRUN_API_KEY", "env-key")
    assert Outrun().api_key == "env-key"


def test_missing_key():
    with pytest.raises(OutrunError):
        Outrun()
    with pytest.raises(OutrunError):
        AsyncOutrun()


def test_ask_returns_content_and_sends_system():
    seen = []
    c = client(seen)
    assert c.ask("some-model", "hi", system="be brief") == "hello there"
    body = json.loads(seen[0].content)
    assert body["model"] == "some-model"
    assert body["messages"] == [
        {"role": "system", "content": "be brief"}, {"role": "user", "content": "hi"}]
    assert str(seen[0].url) == "https://api.outrun.to/v1/chat/completions"
    assert seen[0].headers["authorization"] == "Bearer test-key"


def test_ask_stream_yields_chunks():
    seen = []
    assert list(client(seen).ask_stream("m", "hi")) == ["Hel", "lo"]


def test_sdk_header_present_and_overridable():
    seen = []
    client(seen).ask("m", "hi")
    assert seen[0].headers["x-outrun-sdk"] == "python/0.1.0"
    seen2 = []
    client(seen2, default_headers={"X-Extra": "1"}).ask("m", "hi")
    assert seen2[0].headers["x-extra"] == "1"
    assert seen2[0].headers["x-outrun-sdk"] == "python/0.1.0"


def test_openai_chat_attribute_not_shadowed():
    c = Outrun(api_key="k")
    assert hasattr(c.chat, "completions")
    assert hasattr(c, "models") and hasattr(c, "images")


async def test_async_ask_and_stream():
    seen = []
    c = AsyncOutrun(api_key="k", http_client=httpx.AsyncClient(
        transport=httpx.MockTransport(make_handler(seen))))
    assert await c.ask("m", "hi") == "hello there"
    assert [t async for t in c.ask_stream("m", "hi")] == ["Hel", "lo"]
    assert seen[0].headers["x-outrun-sdk"] == "python/0.1.0"
