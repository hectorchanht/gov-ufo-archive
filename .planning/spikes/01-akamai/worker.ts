/**
 * Akamai Egress Spike — Cloudflare Worker probe lane.
 *
 * Plan: .planning/phases/01-pre-migration-safety/01-03-PLAN.md (PMS-03).
 * Decision target: .planning/decisions/akamai-spike.md (D-12 — first ADR).
 * Companion: .planning/spikes/01-akamai/actions-runner.py (Actions lane).
 *
 * Goal: prove or disprove the .planning/research/PITFALLS.md Pitfall #3 hypothesis
 * that Cloudflare Worker egress is blocked by Akamai (war.gov, aaro.mil) MORE
 * aggressively than GitHub Actions runners — per-source, with raw rows captured
 * so .planning/decisions/akamai-spike.md can compute success rate against the
 * D-11 threshold (Workers viable iff success ≥ 95% AND ≥ Actions success).
 *
 * Schedule contract (see README.md "How to run the Worker lane"):
 *   wrangler.toml cron:  "* * * * *"   (every 1 minute)
 *   per cron firing, fetch ONE round = 1 fetch per target = 5 fetches.
 *   100 firings × 5 = 500 rows over ~100 minutes; trim to first 100 per
 *   source post-run with `wrangler kv:key list` filter (see README).
 *
 * Alternatively (single shot mode):
 *   curl -X POST https://<worker>.workers.dev/run-now
 *   runs ONE round of 5 fetches immediately and writes 5 rows; loop externally
 *   100 times with `for i in $(seq 1 100); do curl …/run-now; sleep 36; done`.
 *
 * No third-party packages — pure Workers fetch + KV.
 *
 * UA contract: the Chrome-131 string from .planning/codebase/CONCERNS.md is
 * injected via wrangler.toml [vars] USER_AGENT so it remains a single source
 * of truth shared with the Actions lane. The literal string is:
 *   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
 */

export interface Env {
  SPIKE_RESULTS: KVNamespace;
  PROBE_TARGETS_JSON: string; // wrangler.toml [vars] — paste probe-sources.json's probe_targets array
  USER_AGENT: string;         // wrangler.toml [vars] — paste probe-sources.json's user_agent verbatim
}

interface ProbeRow {
  lane: "worker";
  target_url: string;
  iso_timestamp: string;
  http_status: number;
  body_length_bytes: number;
  latency_ms: number;
  server_header: string | null;
  akamai_cookie_present: boolean;
  akamai_cookie_names: string[];
  body_fingerprint_pardon_our_interruption: boolean;
  body_fingerprint_access_denied: boolean;
  error: string | null;
}

const AKAMAI_COOKIE_NEEDLES = ["_abck=", "bm_sc=", "AKAM_SC="];
const PARDON_NEEDLE = "Pardon Our Interruption";
const DENIED_NEEDLE = "Access Denied";

async function probeOnce(url: string, ua: string): Promise<ProbeRow> {
  const started = Date.now();
  const isoTs = new Date(started).toISOString();
  try {
    const resp = await fetch(url, {
      method: "GET",
      redirect: "manual",
      headers: {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
    });
    const latency = Date.now() - started;
    // Read up to first 2 KB of body for fingerprint without inflating Worker memory.
    const reader = resp.body?.getReader();
    let buf = new Uint8Array(0);
    let totalLen = 0;
    if (reader) {
      const sample: Uint8Array[] = [];
      let sampleBytes = 0;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        totalLen += value.byteLength;
        if (sampleBytes < 2048) {
          sample.push(value);
          sampleBytes += value.byteLength;
        }
      }
      // Concatenate first 2 KB only.
      buf = new Uint8Array(Math.min(sampleBytes, 2048));
      let off = 0;
      for (const chunk of sample) {
        if (off >= buf.byteLength) break;
        const take = Math.min(chunk.byteLength, buf.byteLength - off);
        buf.set(chunk.subarray(0, take), off);
        off += take;
      }
    }
    const bodySnippet = new TextDecoder("utf-8", { fatal: false }).decode(buf);
    const setCookie = resp.headers.get("Set-Cookie") ?? "";
    const cookieHits = AKAMAI_COOKIE_NEEDLES.filter((n) => setCookie.includes(n));
    return {
      lane: "worker",
      target_url: url,
      iso_timestamp: isoTs,
      http_status: resp.status,
      body_length_bytes: totalLen,
      latency_ms: latency,
      server_header: resp.headers.get("Server"),
      akamai_cookie_present: cookieHits.length > 0,
      akamai_cookie_names: cookieHits,
      body_fingerprint_pardon_our_interruption: bodySnippet.includes(PARDON_NEEDLE),
      body_fingerprint_access_denied: bodySnippet.includes(DENIED_NEEDLE),
      error: null,
    };
  } catch (e: unknown) {
    return {
      lane: "worker",
      target_url: url,
      iso_timestamp: isoTs,
      http_status: 0,
      body_length_bytes: 0,
      latency_ms: Date.now() - started,
      server_header: null,
      akamai_cookie_present: false,
      akamai_cookie_names: [],
      body_fingerprint_pardon_our_interruption: false,
      body_fingerprint_access_denied: false,
      error: e instanceof Error ? `${e.name}: ${e.message}` : String(e),
    };
  }
}

async function runOneRound(env: Env): Promise<ProbeRow[]> {
  const targets: string[] = JSON.parse(env.PROBE_TARGETS_JSON);
  // Parallel fetch — 5 targets per round, well under Worker subrequest budget.
  const rows = await Promise.all(targets.map((t) => probeOnce(t, env.USER_AGENT)));
  // Write each row to KV under worker:<iso>:<host>. Hash via simple host slug.
  await Promise.all(
    rows.map(async (r) => {
      const host = new URL(r.target_url).host.replace(/[^a-z0-9.-]/gi, "_");
      const key = `worker:${r.iso_timestamp}:${host}`;
      await env.SPIKE_RESULTS.put(key, JSON.stringify(r), {
        // Auto-expire 30 days post-spike so KV doesn't accumulate.
        expirationTtl: 60 * 60 * 24 * 30,
      });
    }),
  );
  return rows;
}

export default {
  // Cron trigger — see wrangler.toml `[triggers] crons = ["* * * * *"]`.
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(runOneRound(env).then(() => {}));
  },
  // HTTP entry — manual `/run-now` invocation for ad-hoc rounds during sanity-check.
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === "/run-now") {
      const rows = await runOneRound(env);
      return Response.json({ rows_written: rows.length, rows });
    }
    return new Response(
      "Akamai spike Worker — POST /run-now for one round, or rely on the cron trigger.\n" +
        "See .planning/spikes/01-akamai/README.md for the full runbook.",
      { status: 200, headers: { "content-type": "text/plain" } },
    );
  },
};
