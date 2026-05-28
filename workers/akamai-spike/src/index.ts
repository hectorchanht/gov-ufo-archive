/// <reference types="@cloudflare/workers-types" />
//
// realufo-akamai-spike — one-shot probe Worker.
// Plan 05-02 scope. Throwaway: deleted after `.planning/decisions/akamai-spike.md` locks.
//
// Fetches the 4 active realufo source origins from a Cloudflare Workers IP
// and records HTTP status + response signature. Results are written to KV
// (binding `AKAMAI_SPIKE`, key `last-spike-result`, 24h TTL) and returned
// as JSON to the caller.

interface Env {
  AKAMAI_SPIKE: KVNamespace;
}

interface SourceProbe {
  slug: string;
  url: string;
}

interface ProbeResult {
  slug: string;
  url: string;
  status: number | null;
  server: string | null;
  akamai: string | null;
  cfRay: string | null;
  latencyMs: number;
  errorMsg?: string;
}

// 4 active source origins (CLAUDE.md §2 + 05-CONTEXT.md D-10).
const SOURCES: ReadonlyArray<SourceProbe> = [
  { slug: "wargov", url: "https://www.war.gov/UFO/" },
  { slug: "aaro", url: "https://www.aaro.mil/Cases/" },
  { slug: "nasa", url: "https://science.nasa.gov/uap/" },
  { slug: "nara", url: "https://catalog.archives.gov/" },
];

// Realistic Chrome UA — matches what a production cron Worker would send
// so Akamai sees the same blocking surface. See 05-02-PLAN.md <interfaces>.
const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

async function probe(source: SourceProbe): Promise<ProbeResult> {
  const t0 = Date.now();
  try {
    const res = await fetch(source.url, {
      headers: {
        "User-Agent": UA,
        Accept: "text/html,*/*",
      },
      redirect: "follow",
      cf: { cacheTtl: 0 },
    });
    return {
      slug: source.slug,
      url: source.url,
      status: res.status,
      server: res.headers.get("server"),
      akamai: res.headers.get("x-akamai-transformed"),
      cfRay: res.headers.get("cf-ray"),
      latencyMs: Date.now() - t0,
    };
  } catch (err) {
    return {
      slug: source.slug,
      url: source.url,
      status: null,
      server: null,
      akamai: null,
      cfRay: null,
      latencyMs: Date.now() - t0,
      errorMsg: err instanceof Error ? err.message : String(err),
    };
  }
}

export default {
  async fetch(_request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    // Run the 4 probes in parallel — Plan 05-04 may use this latency data
    // to decide serial vs parallel scrape-lane fan-out (CONTEXT.md
    // §Claude's Discretion).
    const settled = await Promise.all(SOURCES.map(probe));

    const results: Record<string, ProbeResult> = {};
    for (const r of settled) results[r.slug] = r;

    const payload = {
      runAt: new Date().toISOString(),
      ua: UA,
      results,
    };
    const body = JSON.stringify(payload, null, 2);

    // Persist for operator transcription into akamai-spike.md (Task 3).
    // 24h TTL — throwaway.
    await env.AKAMAI_SPIKE.put("last-spike-result", body, { expirationTtl: 86400 });

    // 60s edge cache absorbs operator re-polls without re-charging fetches
    // against the upstream sites (T-05-02-03 mitigation).
    return new Response(body, {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "public, max-age=60",
      },
    });
  },
} satisfies ExportedHandler<Env>;
