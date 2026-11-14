import { test } from "node:test";
import assert from "node:assert/strict";
import { prices, PRICING_URL } from "../dist/index.js";

const FEED = {
  currency: "USD",
  generated_at: 1,
  paused: ["paused-model"],
  models: [
    { id: "text-a", name: "Text A", family: "f", kind: "text", unit: "1M tokens",
      tiers: [{ label: "all", unit: "1M tokens", prices: { input: 0.1, output: 0.4 } }] },
    { id: "img-b", name: "Image B", family: "image", kind: "image", unit: "image",
      tiers: [{ label: "all", unit: "image", prices: { output: 0.02 } }] },
    { id: "paused-model", name: "Paused", family: "f", kind: "text", unit: "1M tokens", tiers: [] },
  ],
};

// In-memory fetch: no test touches the network.
function mock(body = FEED, status = 200) {
  const seen = [];
  const fetch = async (url, init) => {
    seen.push({ url: String(url), headers: new Headers(init?.headers) });
    return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  };
  return { seen, fetch };
}

test("feed URL constant", () => {
  assert.equal(PRICING_URL, "https://api.outrun.to/pricing");
});

test("returns active models with paused flag", async () => {
  const m = mock();
  const out = await prices({ fetch: m.fetch });
  assert.deepEqual(out.map((x) => x.id), ["text-a", "img-b"]);
  assert.ok(out.every((x) => x.paused === false));
  assert.equal(out[0].tiers[0].prices.output, 0.4);
});

test("kind filter and includePaused", async () => {
  const m = mock();
  assert.deepEqual((await prices({ kind: "text", fetch: m.fetch })).map((x) => x.id), ["text-a"]);
  const both = await prices({ kind: "text", includePaused: true, fetch: m.fetch });
  assert.deepEqual(both.map((x) => [x.id, x.paused]), [["text-a", false], ["paused-model", true]]);
});

test("request URL, user agent, no key", async () => {
  const m = mock();
  await prices({ fetch: m.fetch });
  assert.equal(m.seen[0].url, "https://api.outrun.to/pricing");
  const ua = m.seen[0].headers.get("user-agent");
  assert.ok(ua.startsWith("Mozilla/5.0") && ua.includes("outrun-ai-node/"));
  assert.equal(m.seen[0].headers.get("authorization"), null);
  assert.equal(FEED.models[0].paused, undefined);
});

test("HTTP error becomes a clear error", async () => {
  const m = mock({ error: "no" }, 403);
  await assert.rejects(prices({ fetch: m.fetch }), /price list.*HTTP 403/);
});

test("bad format becomes a clear error", async () => {
  const m = mock({ unexpected: true });
  await assert.rejects(prices({ fetch: m.fetch }), /format/);
});
