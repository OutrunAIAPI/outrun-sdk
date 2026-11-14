import OpenAI, { type ClientOptions } from "openai";

export const VERSION = "0.1.0";
export const DEFAULT_BASE_URL = "https://api.outrun.to/v1";

export type OutrunOptions = Omit<ClientOptions, "apiKey" | "baseURL"> & {
  apiKey?: string;
  baseURL?: string;
};

export type AskOptions = {
  system?: string;
  [param: string]: unknown;
};

function messages(prompt: string, system?: string) {
  const out: { role: "system" | "user"; content: string }[] = [];
  if (system) out.push({ role: "system", content: system });
  out.push({ role: "user", content: prompt });
  return out;
}

/** OpenAI client defaulting to the Outrun API. Everything on OpenAI still works. */
export class Outrun extends OpenAI {
  constructor(opts: OutrunOptions = {}) {
    const apiKey = opts.apiKey ?? process.env.OUTRUN_API_KEY;
    if (!apiKey) {
      throw new Error(
        "No API key. Pass { apiKey } or set the OUTRUN_API_KEY environment variable. " +
          "Get a key at https://outrun.to/key",
      );
    }
    super({
      ...opts,
      apiKey,
      baseURL: opts.baseURL ?? DEFAULT_BASE_URL,
      defaultHeaders: { "X-Outrun-SDK": `node/${VERSION}`, ...(opts.defaultHeaders as object) },
    });
  }

  /** Send one prompt, return the reply text. */
  async ask(model: string, prompt: string, options: AskOptions = {}): Promise<string> {
    const { system, ...rest } = options;
    const r: any = await this.chat.completions.create({
      ...rest,
      model,
      messages: messages(prompt, system),
      stream: false,
    } as any);
    return r.choices[0]?.message?.content ?? "";
  }

  /** Send one prompt, yield reply text as it arrives. */
  async *askStream(model: string, prompt: string, options: AskOptions = {}): AsyncGenerator<string> {
    const { system, ...rest } = options;
    const stream: any = await this.chat.completions.create({
      ...rest,
      model,
      messages: messages(prompt, system),
      stream: true,
    } as any);
    for await (const chunk of stream) {
      const text = chunk.choices?.[0]?.delta?.content;
      if (text) yield text;
    }
  }
}

export const PRICING_URL = "https://api.outrun.to/pricing";

export type PriceTier = {
  label: string;
  unit: string;
  prices: Record<string, number>;
  [field: string]: unknown;
};

export type ModelPrice = {
  id: string;
  name: string;
  family: string;
  kind: string;
  unit: string;
  tiers: PriceTier[];
  paused: boolean;
  [field: string]: unknown;
};

export type PricesOptions = {
  /** Only return models of this kind, for example "text". */
  kind?: string;
  /** Also return models that are paused right now. */
  includePaused?: boolean;
  /** Milliseconds to wait for the feed (default 15000). */
  timeoutMs?: number;
  /** Feed URL. Only change this for testing. */
  url?: string;
  /** Custom fetch implementation. Defaults to the global fetch. */
  fetch?: typeof fetch;
};

/** Public Outrun price list. No API key is needed and nothing is billed. */
export async function prices(options: PricesOptions = {}): Promise<ModelPrice[]> {
  const url = options.url ?? PRICING_URL;
  const doFetch = options.fetch ?? globalThis.fetch;
  let feed: any;
  try {
    const res = await doFetch(url, {
      headers: {
        "User-Agent": `Mozilla/5.0 (compatible; outrun-ai-node/${VERSION}; +https://outrun.to)`,
        Accept: "application/json",
      },
      signal: AbortSignal.timeout(options.timeoutMs ?? 15000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    feed = await res.json();
  } catch (err) {
    throw new Error(`Could not read the Outrun price list from ${url}: ${(err as Error).message}`);
  }
  if (!feed || !Array.isArray(feed.models)) {
    throw new Error(`Unexpected price list format from ${url}`);
  }
  const paused = new Set<string>(Array.isArray(feed.paused) ? feed.paused : []);
  const out: ModelPrice[] = [];
  for (const model of feed.models) {
    if (!model || typeof model.id !== "string") continue;
    const item = { ...model, paused: paused.has(model.id) } as ModelPrice;
    if (item.paused && !options.includePaused) continue;
    if (options.kind !== undefined && item.kind !== options.kind) continue;
    out.push(item);
  }
  return out;
}

export default Outrun;
