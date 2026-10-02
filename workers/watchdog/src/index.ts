/// <reference types="@cloudflare/workers-types" />
//
// realufo-watchdog — daily health check for realufo.org.
//
// 1. Assets: every R2 key the deployed site links to (dist/watchdog.json,
//    written by scripts/build-watchdog-index.py) must exist in the `realufo`
//    bucket with non-zero size, and assets.realufo.org must serve them.
// 2. New release: any "Release Date" in war.gov's uap-data.csv that the site
//    doesn't have yet = a new war.gov release to ingest. war.gov sits behind
//    Akamai; if the direct fetch is blocked, fall back to the latest Wayback
//    snapshot.
//
// Problems open (or update) one GitHub issue labelled `watchdog`; a clean run
// closes it. GET on the Worker URL returns the same report as JSON without
// touching GitHub — the "check now" button.

interface Env {
  BUCKET: R2Bucket;
  SITE: string;
  ASSETS_ORIGIN: string;
  GITHUB_REPO: string;
  GITHUB_TOKEN?: string;
}

interface Report {
  ok: boolean;
  problems: string[];
  notes: string[];
}

const CSV_URL = "https://www.war.gov/Portals/1/Interactive/2026/UFO/uap-data.csv";
const UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36";
const ISSUE_TITLE = "Watchdog: realufo.org needs attention";
const LABEL = "watchdog";
const MAX_LISTED = 100;

// Minimal RFC 4180 parser — the war.gov CSV has quoted, multi-line blurbs.
function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c !== '"') field += c;
      else if (text[i + 1] === '"') { field += '"'; i++; }
      else quoted = false;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); rows.push(row); row = []; field = "";
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

function releaseDates(csv: string): Set<string> {
  const [header, ...rows] = parseCsv(csv.replace(/^﻿/, ""));
  const col = header.indexOf("Release Date");
  if (col < 0) throw new Error("war.gov CSV has no 'Release Date' column");
  return new Set(rows.map((r) => (r[col] ?? "").trim()).filter(Boolean));
}

async function fetchWargovCsv(): Promise<{ text: string; via: string }> {
  const direct = await fetch(CSV_URL, { headers: { "User-Agent": UA, Accept: "text/csv,*/*" } });
  if (direct.ok) return { text: await direct.text(), via: "war.gov" };

  const avail = (await (await fetch(`https://archive.org/wayback/available?url=${encodeURIComponent(CSV_URL)}`)).json()) as {
    archived_snapshots?: { closest?: { timestamp: string; available: boolean } };
  };
  const snap = avail.archived_snapshots?.closest;
  if (!snap?.available) throw new Error(`war.gov returned ${direct.status} and Wayback has no snapshot`);
  const wb = await fetch(`https://web.archive.org/web/${snap.timestamp}id_/${CSV_URL}`);
  if (!wb.ok) throw new Error(`war.gov returned ${direct.status}, Wayback returned ${wb.status}`);
  return { text: await wb.text(), via: `Wayback snapshot ${snap.timestamp} (war.gov returned ${direct.status})` };
}

async function listSizes(bucket: R2Bucket): Promise<Map<string, number>> {
  const sizes = new Map<string, number>();
  let cursor: string | undefined;
  do {
    const page = await bucket.list({ cursor, limit: 1000 });
    for (const o of page.objects) sizes.set(o.key, o.size);
    cursor = page.truncated ? page.cursor : undefined;
  } while (cursor);
  return sizes;
}

function bullets(items: string[]): string {
  const shown = items.slice(0, MAX_LISTED).map((k) => `  - \`${k}\``);
  if (items.length > MAX_LISTED) shown.push(`  - …and ${items.length - MAX_LISTED} more`);
  return shown.join("\n");
}

async function check(env: Env): Promise<Report> {
  const problems: string[] = [];
  const notes: string[] = [];

  const idxRes = await fetch(`${env.SITE}/watchdog.json`, { cf: { cacheTtl: 0 } });
  if (!idxRes.ok) {
    return { ok: false, problems: [`\`${env.SITE}/watchdog.json\` returned ${idxRes.status}. Is the latest build deployed?`], notes };
  }
  const idx = (await idxRes.json()) as { assets: string[]; wargovReleaseDates: string[] };

  // 1. Assets.
  try {
    const sizes = await listSizes(env.BUCKET);
    const missing = idx.assets.filter((k) => !sizes.has(k));
    const empty = idx.assets.filter((k) => sizes.get(k) === 0);
    if (missing.length) problems.push(`**${missing.length} linked assets missing from R2** (they 404 on the site):\n${bullets(missing)}`);
    if (empty.length) problems.push(`**${empty.length} assets are 0 bytes in R2:**\n${bullets(empty)}`);
    notes.push(`${idx.assets.length - missing.length}/${idx.assets.length} linked assets present in R2 (${sizes.size} objects in bucket).`);

    // One public probe catches a broken custom domain / CORS / cache rule.
    const probeKey = idx.assets.find((k) => sizes.has(k));
    if (probeKey) {
      const probe = await fetch(`${env.ASSETS_ORIGIN}/${probeKey}`, { method: "HEAD" });
      if (!probe.ok) problems.push(`**Public asset domain broken:** HEAD \`${env.ASSETS_ORIGIN}/${probeKey}\` returned ${probe.status}, even though the object exists in R2.`);
    }
  } catch (e) {
    problems.push(`**Asset check failed:** ${(e as Error).message}`);
  }

  // 2. New war.gov release.
  try {
    const { text, via } = await fetchWargovCsv();
    const have = new Set(idx.wargovReleaseDates);
    const upstream = [...releaseDates(text)];
    const fresh = upstream.filter((d) => !have.has(d));
    if (fresh.length) {
      problems.push(`**New war.gov release detected:** release date(s) ${fresh.map((d) => `\`${d}\``).join(", ")} are in war.gov's \`uap-data.csv\` but not on realufo.org (source: ${via}). Ingest it with the release recipe.`);
    }
    notes.push(`war.gov CSV checked via ${via}: ${upstream.length} release dates upstream, ${have.size} on site.`);
  } catch (e) {
    problems.push(`**war.gov release check failed:** ${(e as Error).message}`);
  }

  return { ok: problems.length === 0, problems, notes };
}

async function gh(env: Env, path: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "realufo-watchdog",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
    },
  });
  if (!res.ok) throw new Error(`GitHub ${init.method ?? "GET"} ${path} returned ${res.status}: ${await res.text()}`);
  return res;
}

// One open issue at a time. Body is rewritten only when the findings change,
// with a comment so the change notifies watchers; a clean run closes it.
async function syncIssue(env: Env, report: Report): Promise<void> {
  if (!env.GITHUB_TOKEN) throw new Error("GITHUB_TOKEN secret not set");
  const open = (await (await gh(env, `/issues?state=open&labels=${LABEL}&per_page=1`)).json()) as { number: number; body: string }[];
  const issue = open[0];
  const body = `${report.problems.join("\n\n")}\n\n---\n${report.notes.map((n) => `- ${n}`).join("\n")}\n\n_Filed by the \`realufo-watchdog\` Worker (daily cron)._`;

  if (!report.ok && !issue) {
    await gh(env, "/issues", { method: "POST", body: JSON.stringify({ title: ISSUE_TITLE, body, labels: [LABEL] }) });
  } else if (!report.ok && issue && issue.body.split("\n---\n")[0] !== body.split("\n---\n")[0]) {
    await gh(env, `/issues/${issue.number}`, { method: "PATCH", body: JSON.stringify({ body }) });
    await gh(env, `/issues/${issue.number}/comments`, { method: "POST", body: JSON.stringify({ body: "Findings changed. Issue body updated." }) });
  } else if (report.ok && issue) {
    await gh(env, `/issues/${issue.number}/comments`, { method: "POST", body: JSON.stringify({ body: `All checks pass.\n\n${report.notes.map((n) => `- ${n}`).join("\n")}` }) });
    await gh(env, `/issues/${issue.number}`, { method: "PATCH", body: JSON.stringify({ state: "closed" }) });
  }
}

export default {
  async fetch(_req: Request, env: Env): Promise<Response> {
    return Response.json(await check(env));
  },

  async scheduled(_event: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(
      (async () => {
        const report = await check(env);
        console.log(JSON.stringify(report));
        await syncIssue(env, report);
      })(),
    );
  },
} satisfies ExportedHandler<Env>;
