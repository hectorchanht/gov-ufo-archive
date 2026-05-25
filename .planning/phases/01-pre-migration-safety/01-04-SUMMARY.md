---
phase: 01-pre-migration-safety
plan: 04
subsystem: dns
tags: [dns, ttl, porkbun, phase6-gate, pre-migration]
status: partial-checkpoint
requires:
  - .planning/phases/01-pre-migration-safety/01-04-PLAN.md
  - .planning/research/PITFALLS.md#pitfall-15
  - .planning/phases/01-pre-migration-safety/01-CONTEXT.md#D-17
provides:
  - .planning/decisions/dns-ttl.md
affects:
  - Phase 6 cutover-gate (7-day countdown anchor)
tech-stack:
  added: []
  patterns:
    - "ADR-style decision documents under .planning/decisions/ (second entry; first is akamai-spike.md)"
    - "DNS-provider discovery via dig +trace + whois (replicable, no auth)"
key-files:
  created:
    - .planning/decisions/dns-ttl.md
  modified: []
decisions:
  - "DNS provider for realufo.org is Porkbun (registrar + DNS host — single-vendor), discovered via dig NS + whois."
  - "Current TTL on all five records (4× apex A + 1× www CNAME) is 600 s; target 300 s."
  - "Phase 6 7-day countdown anchors on the ## TTL Change Log timestamp (operator-written), not the ## Verification Log timestamp."
metrics:
  duration: ~6 minutes (Task 1 only — Task 2 awaiting operator)
  completed_date: 2026-05-25
  tasks_completed: 1
  tasks_pending_checkpoint: 1
---

# Phase 01 Plan 04: DNS TTL Drop Summary

**One-liner:** Porkbun DNS discovered as authoritative host for realufo.org; current TTL=600 s on apex A records + www CNAME; operator checkpoint pending to drop TTL to 300 s and anchor Phase 6's 7-day cutover countdown.

## Status

**Partial — checkpoint reached.**

- Task 1 (auto): ✅ Complete — committed as `fe2d539`.
- Task 2 (checkpoint:human-action): ⏸️ Awaiting operator. Cannot be automated — requires authenticated session against Porkbun's dashboard.

## What Was Done (Task 1)

Ran four DNS discovery commands from the worktree (network access confirmed working):

1. `dig +trace realufo.org` — traced the full delegation chain from root → `.org` TLD → Porkbun anycast NS.
2. `dig NS realufo.org +short` — confirmed the four authoritative nameservers are all `*.ns.porkbun.com`.
3. `whois realufo.org` — confirmed registrar is Porkbun LLC (IANA ID 1861).
4. `dig +noall +answer realufo.org` (against system resolver, 1.1.1.1, and 8.8.8.8) — recorded the current TTL=600 s on the four apex A records pointing at GitHub Pages anycast (185.199.108-111.153). Additional check: `dig +noall +answer www.realufo.org` exposed a CNAME (TTL=600) pointing at `hectorchanht.github.io.` — so there are **two record sets to change**, not one.

Wrote `.planning/decisions/dns-ttl.md` with all 9 required sections fully populated with literal command outputs (not placeholders). Automated verification (the regex chain from the plan's `<verify>` block) confirmed all five gates pass:

| Gate | Result |
| ---- | ------ |
| File exists | ✅ |
| ≥9 required `##` sections | ✅ (exactly 9) |
| `realufo.org` mentioned ≥2× | ✅ (42×) |
| Dig-format line `realufo.org. <N> IN (A\|CNAME) <v>` present (W4 fix) | ✅ (18×) |
| No `TBD/TODO/XXX/FIXME` placeholders | ✅ |

## Key Findings

1. **Porkbun is both registrar and DNS host.** The four "Brazilian-city" nameserver names (`curitiba/fortaleza/salvador/maceio.ns.porkbun.com`) are Porkbun's standard anycast naming convention — not a separate Brazilian DNS provider. Single-vendor simplifies the operator's workflow: one login, one dashboard.
2. **Current TTL is already low (600 s), not the typical 3600 s default.** Porkbun's default TTL for new records is 600 s, and these records were never manually tuned. The drop to 300 s is only a 2× reduction in absolute terms, but it's still required to anchor the Phase 6 countdown from a deterministic, known-low timestamp.
3. **Two record sets need changing, not one.** Plan 01-04 originally described "A/CNAME records" generically — the discovered reality is 4× apex A records + 1× `www` CNAME. The procedure in `.planning/decisions/dns-ttl.md` §Provider-Specific Change Procedure enumerates all five edits explicitly.
4. **GH Pages confirmation.** All four apex A records resolve to `185.199.108-111.153` — GitHub Pages' anycast IP block. This confirms the current `realufo.org` apex is served by GH Pages via the four-A-record pattern (per GH's apex-domain setup guide), not a CNAME flattener. The `www` CNAME → `hectorchanht.github.io.` is consistent.

## What Operator Must Do Next (Task 2)

This is a `checkpoint:human-action` task with `gate="blocking"`. The executor presents the operator with the verbatim procedure and HALTS — cannot self-progress because Claude does not have Porkbun dashboard credentials.

### Provider info for the operator

| Field | Value |
| ----- | ----- |
| Provider | Porkbun (registrar + DNS host) |
| Dashboard URL | <https://porkbun.com/account/login> |
| DNS-records deep-link | <https://porkbun.com/account/domainsSpeedy> → `realufo.org` → "Details" → "DNS Records" |
| Records to change | 4× apex A (`@` → 185.199.108-111.153) + 1× `www` CNAME (→ hectorchanht.github.io.) |
| Current TTL | 600 s |
| Target TTL | 300 s |

### Step-by-step (from `.planning/decisions/dns-ttl.md` §Provider-Specific Change Procedure)

1. Log into Porkbun at <https://porkbun.com/account/login>.
2. Navigate to "Domain Management" → click `realufo.org` → click "Details" → click "DNS Records" (or use the DNS deep-link above).
3. Edit each of the **four** apex (`@`) A records (one per `185.199.108-111.153` IP): click the pencil/edit icon → change TTL from `600` to `300` → click "Save".
4. Edit the `www` CNAME record (Type=CNAME, Host=`www`, Answer=`hectorchanht.github.io.`): click pencil/edit → change TTL from `600` to `300` → click "Save".
5. **Update `.planning/decisions/dns-ttl.md`**: under `## TTL Change Log`, append a line:
   ```
   - 2026-MM-DDTHH:MM:SSZ — TTL on realufo.org A records (4×) and www CNAME (1×) dropped from 600 s to 300 s via Porkbun DNS dashboard.
   ```
   And update `## Status` from `discovered` to `dropped`.
6. **Wait 1–2 hours for propagation** (caching resolvers serve the old TTL until their existing cache entry expires — that's the 600 s already in flight).
7. **Verify propagation:**
   ```
   dig +noall +answer realufo.org @1.1.1.1
   dig +noall +answer realufo.org @8.8.8.8
   ```
   Both should report TTL ≤ 300. If they still show 600 after 2 hours, the dashboard save probably didn't take — re-open and check.
8. **Update `.planning/decisions/dns-ttl.md`**: under `## Verification Log`, append two lines with the dig outputs and timestamps. Update `## Status` from `dropped` to `verified`.
9. **Commit `.planning/decisions/dns-ttl.md`** — this finalizes the Phase 6 cutover-gate anchor.

### Resume signal

After step 9 lands a commit with Status=`verified` and populated logs, the operator types **`ttl-verified`** to re-run `/gsd:execute-phase 1` and resume. If anything blocks (TTL won't propagate, dashboard rejects the change, etc.), the operator types **`blocked: <reason>`**.

## Deviations from Plan

None. Plan executed exactly as written for Task 1. The "could be Cloudflare DNS or registrar or third-party" uncertainty in the plan resolved cleanly to "Porkbun is both registrar and DNS host."

Note: The plan's `<interfaces>` block mentioned anticipated patterns (`*.ns.cloudflare.com`, `dns*.registrar-servers.com`, etc.) but did not list Porkbun's pattern (`*.ns.porkbun.com`). The discovered provider matched none of the anticipated patterns from `<interfaces>`, which is the exact reason Task 1 is a discovery task rather than a hard-coded procedure. The discovered provider name was added to the decision doc verbatim per the plan's discovery-evidence requirement.

## Authentication Gates

Task 2 is itself an authentication gate by design — Porkbun's DNS dashboard requires the operator's account credentials. This is the canonical `checkpoint:human-action` shape (1% case): a single unavoidable manual step that cannot be automated regardless of CLI tooling.

## Known Stubs

None. Both `## TTL Change Log` and `## Verification Log` are intentionally placeholder-empty (with HTML-comment examples showing the expected format) — they will be populated by the operator in Task 2 step 5 and step 8 respectively. These are not stubs in the "shipped with broken UI" sense; they are intentional checkpoints in a workflow document.

The grep `'TBD|TODO|XXX|FIXME'` check confirms no shippable-content placeholders.

## Threat Flags

None. The threat register in the plan covered all surfaces (DNS read-only queries, operator-driven change, repudiation via public dig audit trail). No new surface was introduced.

## Files Created

- `.planning/decisions/dns-ttl.md` — 229 lines, 9 sections, captures Porkbun discovery + change procedure + Phase 6 countdown anchor. Committed as `fe2d539`.

## Commits

| Hash | Type | Message |
| ---- | ---- | ------- |
| `fe2d539` | docs(01-04) | discover DNS provider + scaffold dns-ttl.md |

## Self-Check: PASSED

- ✅ `.planning/decisions/dns-ttl.md` exists at expected path.
- ✅ `fe2d539` commit exists in `git log`.
- ✅ All 9 required sections present in the file (`grep -cE '^## (...)' = 9`).
- ✅ Dig-format `realufo.org. <N> IN (A|CNAME) <v>` line present (18×, satisfies W4 ≥1 fix).
- ✅ No `TBD/TODO/XXX/FIXME` placeholders.
- ✅ DNS Provider section names a concrete provider (Porkbun), not "unknown" or "TBD".
- ✅ Provider-Specific Change Procedure has 4 concrete dashboard steps (apex × 4 edits + www CNAME × 1 edit), not generic prose.
