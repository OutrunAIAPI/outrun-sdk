# outrun-ai (Node / TypeScript)

Node client for the [Outrun API](https://outrun.to). Outrun is a prepaid, OpenAI-compatible API: one key for GPT, Claude, Gemini, Grok, DeepSeek, GLM, Kimi, Qwen and MiniMax models. This package is a thin wrapper over the official `openai` npm package with the base URL and API key set for you, so everything the OpenAI SDK does still works. ESM, with TypeScript types. Node 18 or newer.

## Install

```bash
npm install outrun-ai
```

## Quickstart

Create a key at https://outrun.to/key, then:

```bash
export OUTRUN_API_KEY="your-key"
```

```js
import { Outrun } from "outrun-ai";

const client = new Outrun(); // reads OUTRUN_API_KEY
console.log(await client.ask("gpt-5.6-terra", "Say hello in five words."));
console.log(await client.ask("deepseek-v4.1-flash", "Name three prime numbers.", { system: "Be brief." }));
```

You can also pass `new Outrun({ apiKey: "...", baseURL: "..." })`. The default base URL is `https://api.outrun.to/v1`. If no key is found, the constructor throws.

## Streaming

```js
for await (const text of client.askStream("deepseek-v4.1-flash", "Write a haiku about rain.")) {
  process.stdout.write(text);
}
```

## Model ids and prices

`prices()` reads the public price list. It needs no key and costs nothing.

```js
import { prices } from "outrun-ai";

for (const m of await prices({ kind: "text" })) {
  const tier = m.tiers[0];
  console.log(m.id, tier.prices.input, tier.prices.output, "USD per", tier.unit);
}
```

Each item has `id` (the model name to send), `name`, `family`, `kind` (`text`, `image`, `video` or `audio`), `unit`, `tiers` and `paused`. Paused models are left out unless you pass `includePaused: true`. The same list is at https://outrun.to/pricing.

## Everything else

`Outrun` extends `OpenAI`, so the usual calls work unchanged:

```js
await client.chat.completions.create({
  model: "deepseek-v4.1-flash",
  messages: [{ role: "user", content: "Hi" }],
});
await client.models.list();
```

Extra options for `ask` / `askStream` (such as `temperature` or `max_tokens`) go in the third argument next to `system`.

Each API request carries an `X-Outrun-SDK: node/<version>` header. Nothing else is added.

## Links

- Docs: https://outrun.to/docs/
- Python: `pip install outrun-ai`
- Support: support@outrun.to

License: MIT.
