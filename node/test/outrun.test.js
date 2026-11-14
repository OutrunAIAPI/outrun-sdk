import { test } from "node:test";
import assert from "node:assert/strict";
import { Outrun, DEFAULT_BASE_URL } from "../dist/index.js";

const COMPLETION = {
  id: "c1", object: "chat.completion", created: 1, model: "m",
  choices: [{ index: 0, finish_reason: "stop", message: { role: "assistant", content: "hello there" } }],
};
const chunk = (delta, finish = null) =>
  `data: ${JSON.stringify({ id: "c", object: "chat.completion.chunk", created: 1, model: "m", choices: [{ index: 0, delta, finish_reason: finish }] })}\n\n`;
const SSE = chunk({ role: "assistant", content: "Hel" }) + chunk({ content: "lo" }) + chunk({}, "stop") + "data: [DONE]\n\n";

function mock() {
  const seen = [];
  const fetch = async (url, init) => {
    const body = init?.body ? JSON.parse(init.body) : {};
    seen.push({ url: String(url), headers: new Headers(init?.headers), body });
    return body.stream
      ? new Response(SSE, { status: 200, headers: { "content-type": "text/event-stream" } })
      : new Response(JSON.stringify(COMPLETION), { status: 200, headers: { "content-type": "application/json" } });
  };
  return { seen, fetch };
}

function withEnv(value, fn) {
  const old = process.env.OUTRUN_API_KEY;
  if (value === undefined) delete process.env.OUTRUN_API_KEY; else process.env.OUTRUN_API_KEY = value;
  try { return fn(); } finally { if (old === undefined) delete process.env.OUTRUN_API_KEY; else process.env.OUTRUN_API_KEY = old; }
}

test("default base URL", () => {
  const c = new Outrun({ apiKey: "k" });
  assert.equal(c.baseURL, "https://api.outrun.to/v1");
  assert.equal(DEFAULT_BASE_URL, "https://api.outrun.to/v1");
});

test("custom base URL", () => {
  assert.equal(new Outrun({ apiKey: "k", baseURL: "http://localhost:1/v1" }).baseURL, "http://localhost:1/v1");
});

test("env key pickup", () => {
  withEnv("env-key", () => assert.equal(new Outrun().apiKey, "env-key"));
});

test("missing key throws", () => {
  withEnv(undefined, () => assert.throws(() => new Outrun(), /OUTRUN_API_KEY/));
});

test("ask returns content, sends system, URL, auth", async () => {
  const m = mock();
  const c = new Outrun({ apiKey: "test-key", fetch: m.fetch });
  assert.equal(await c.ask("some-model", "hi", { system: "be brief", temperature: 0 }), "hello there");
  const r = m.seen[0];
  assert.equal(r.url, "https://api.outrun.to/v1/chat/completions");
  assert.equal(r.headers.get("authorization"), "Bearer test-key");
  assert.equal(r.body.model, "some-model");
  assert.equal(r.body.temperature, 0);
  assert.deepEqual(r.body.messages, [{ role: "system", content: "be brief" }, { role: "user", content: "hi" }]);
});

test("askStream yields chunks", async () => {
  const m = mock();
  const c = new Outrun({ apiKey: "k", fetch: m.fetch });
  const out = [];
  for await (const t of c.askStream("m", "hi")) out.push(t);
  assert.deepEqual(out, ["Hel", "lo"]);
});

test("SDK header present, custom headers kept", async () => {
  const m = mock();
  await new Outrun({ apiKey: "k", fetch: m.fetch, defaultHeaders: { "X-Extra": "1" } }).ask("m", "hi");
  assert.equal(m.seen[0].headers.get("x-outrun-sdk"), "node/0.1.0");
  assert.equal(m.seen[0].headers.get("x-extra"), "1");
});

test("OpenAI surface not shadowed", () => {
  const c = new Outrun({ apiKey: "k" });
  assert.equal(typeof c.chat.completions.create, "function");
  assert.equal(typeof c.models.list, "function");
  assert.ok(c.images);
});
