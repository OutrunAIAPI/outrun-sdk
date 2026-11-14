# outrun-ai (Python)

Python client for the [Outrun API](https://outrun.to). Outrun is a prepaid, OpenAI-compatible API: one key for GPT, Claude, Gemini, Grok, DeepSeek, GLM, Kimi, Qwen and MiniMax models. This package is a thin wrapper over the official `openai` package with the base URL and API key set for you, so everything the OpenAI SDK does still works.

## Install

```bash
pip install outrun-ai
```

## Quickstart

Create a key at https://outrun.to/key, then:

```bash
export OUTRUN_API_KEY="your-key"
```

```python
from outrun_ai import Outrun

client = Outrun()  # reads OUTRUN_API_KEY
print(client.ask("gpt-5.6-terra", "Say hello in five words."))
print(client.ask("deepseek-v4.1-flash", "Name three prime numbers.", system="Be brief."))
```

You can also pass `Outrun(api_key="...", base_url="...")`. The default base URL is `https://api.outrun.to/v1`. If no key is found, the client raises `OutrunError`.

## Streaming

```python
for text in client.ask_stream("deepseek-v4.1-flash", "Write a haiku about rain."):
    print(text, end="", flush=True)
```

## Model ids and prices

`prices()` reads the public price list. It needs no key and costs nothing.

```python
from outrun_ai import prices

for m in prices(kind="text"):
    tier = m["tiers"][0]
    print(m["id"], tier["prices"].get("input"), tier["prices"].get("output"), "USD per", tier["unit"])
```

Each item has `id` (the model name to send), `name`, `family`, `kind` (`text`, `image`, `video` or `audio`), `unit`, `tiers` and `paused`. Paused models are left out unless you pass `include_paused=True`. The same list is at https://outrun.to/pricing.

## Everything else

`Outrun` subclasses `openai.OpenAI`, so the usual calls work unchanged:

```python
client.chat.completions.create(
    model="deepseek-v4.1-flash",
    messages=[{"role": "user", "content": "Hi"}],
)
client.models.list()
```

`AsyncOutrun` is the async version (`await client.ask(...)`, `async for t in client.ask_stream(...)`).

Each API request carries an `X-Outrun-SDK: python/<version>` header. Nothing else is added.

## Links

- Docs: https://outrun.to/docs/
- LangChain: `pip install langchain-outrun` ([source](https://github.com/OutrunAIAPI/langchain-outrun))
- Support: support@outrun.to

License: MIT.
