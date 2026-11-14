# Outrun SDKs

Thin client libraries for the [Outrun API](https://outrun.to), a prepaid, OpenAI-compatible API: one key for GPT, Claude, Gemini, Grok, DeepSeek, GLM, Kimi, Qwen and MiniMax models.

Both packages wrap the official OpenAI SDK with the Outrun base URL (`https://api.outrun.to/v1`) and your `OUTRUN_API_KEY`, and add `prices()` for the public price list.

| Language | Package | Install | Source |
|---|---|---|---|
| Python | [`outrun-ai`](https://pypi.org/project/outrun-ai/) | `pip install outrun-ai` | [`python/`](python/) |
| Node / TypeScript | [`outrun-ai`](https://www.npmjs.com/package/outrun-ai) | `npm install outrun-ai` | [`node/`](node/) |

For LangChain, use [`langchain-outrun`](https://github.com/OutrunAIAPI/langchain-outrun).

```python
from outrun_ai import Outrun

client = Outrun()  # reads OUTRUN_API_KEY
print(client.ask("gpt-5.6-terra", "Say hello in five words."))
```

Get a key at https://outrun.to/key. Docs: https://outrun.to/docs/. Support: support@outrun.to.

## Tests

Tests use in-memory mocks and never call the paid API.

```bash
cd python && pip install -e ".[test]" && pytest
cd node && npm install && npm test
```

License: MIT.
