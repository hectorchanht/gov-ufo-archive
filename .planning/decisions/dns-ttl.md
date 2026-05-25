# DNS TTL Decision — realufo.org

This is the second ADR-style decision document under `.planning/decisions/`
(the first is `akamai-spike.md`, produced in plan 01-03). It records WHICH
DNS provider serves `realufo.org`, WHEN the TTL was dropped to 300 s, and
the `dig` outputs confirming propagation. Phase 6's cutover-gate reads the
`## TTL Change Log` timestamp here to enforce the 7-day countdown
(`.planning/ROADMAP.md` §Cross-Phase Dependencies #3,
`.planning/research/PITFALLS.md` Pitfall #15).

## Status

`migration-pending` — Task 1 complete (Porkbun DNS discovered). Decision
revised 2026-05-25: migrate DNS authority Porkbun → Cloudflare DNS before
TTL drop, since Phase 2 hosts the site on Cloudflare Pages and the zone is
already imported into the user's CF account (account
`f1868a071996e836eae6da2b65f37929`). New Task 2 path: change NS at Porkbun
registrar → CF NS, wait for propagation, then set TTL=300 in CF DNS dash.
Transitions: `migration-pending` → `ns-changed` → `dns-on-cloudflare` →
`ttl-dropped` → `verified`.

## DNS Provider

**Porkbun** — registrar + authoritative DNS host (single-vendor).

- Registrar: Porkbun LLC (IANA ID 1861)
- Authoritative nameservers (4): `curitiba.ns.porkbun.com.`,
  `fortaleza.ns.porkbun.com.`, `salvador.ns.porkbun.com.`,
  `maceio.ns.porkbun.com.`
- Dashboard URL: <https://porkbun.com/account/login>
- DNS-management deep-link (after login):
  <https://porkbun.com/account/domainsSpeedy> → `realufo.org` → "Details" →
  "DNS Records"
- Registrar abuse contact: abuse@porkbun.com / +1.8557675286
- Registrar WHOIS server: <http://whois.porkbun.com>

(Note: the four "Brazilian-city" nameserver names —
`curitiba/fortaleza/salvador/maceio` — are Porkbun's standard anycast NS
naming convention, not a separate Brazilian DNS provider. This was
confirmed against `whois realufo.org`, which lists Porkbun as both the
Registrar and the only Name Servers.)

## Discovery Evidence

`dig NS realufo.org +short` (captured 2026-05-25T04:20:13Z from the
agent's local resolver — confirmed cross-checked against the org-tld
delegation in `dig +trace`):

```
curitiba.ns.porkbun.com.
fortaleza.ns.porkbun.com.
maceio.ns.porkbun.com.
salvador.ns.porkbun.com.
```

`whois realufo.org | grep -iE 'name server|registrar|nserver'` (relevant
lines):

```
Registrar WHOIS Server: http://whois.porkbun.com
Registrar URL: https://porkbun.com
Registrar: Porkbun LLC
Registrar IANA ID: 1861
Name Server: maceio.ns.porkbun.com
Name Server: curitiba.ns.porkbun.com
Name Server: salvador.ns.porkbun.com
Name Server: fortaleza.ns.porkbun.com
```

`dig +trace realufo.org` (relevant tail — delegation from `.org` →
Porkbun nameservers → A records):

```
realufo.org.		3600	IN	NS	curitiba.ns.porkbun.com.
realufo.org.		3600	IN	NS	fortaleza.ns.porkbun.com.
realufo.org.		3600	IN	NS	salvador.ns.porkbun.com.
realufo.org.		3600	IN	NS	maceio.ns.porkbun.com.
realufo.org.		600	IN	A	185.199.109.153
realufo.org.		600	IN	A	185.199.108.153
realufo.org.		600	IN	A	185.199.111.153
realufo.org.		600	IN	A	185.199.110.153
;; Received 104 bytes from 162.159.10.150#53(salvador.ns.porkbun.com)
```

The four `185.199.108-111.153` addresses are GitHub Pages' anycast IP
block — confirming the apex points at GitHub Pages via four A records
(per GitHub's "apex domain" setup guide), not at a CNAME flattener.

Additional discovery: `www.realufo.org` is a CNAME, not an A record:

```
www.realufo.org.	600	IN	CNAME	hectorchanht.github.io.
```

So there are **TWO** record sets that need TTL changes:

1. Apex `@` — four A records (185.199.108-111.153)
2. `www` — one CNAME record → `hectorchanht.github.io.`

## Current TTL (pre-change)

`dig +noall +answer realufo.org` (captured 2026-05-25T04:20:13Z from the
agent's local resolver):

```
realufo.org.		600	IN	A	185.199.110.153
realufo.org.		600	IN	A	185.199.109.153
realufo.org.		600	IN	A	185.199.111.153
realufo.org.		600	IN	A	185.199.108.153
```

`dig +noall +answer realufo.org @1.1.1.1` (Cloudflare resolver):

```
realufo.org.		600	IN	A	185.199.110.153
realufo.org.		600	IN	A	185.199.109.153
realufo.org.		600	IN	A	185.199.111.153
realufo.org.		600	IN	A	185.199.108.153
```

`dig +noall +answer realufo.org @8.8.8.8` (Google resolver):

```
realufo.org.		600	IN	A	185.199.108.153
realufo.org.		600	IN	A	185.199.110.153
realufo.org.		600	IN	A	185.199.109.153
realufo.org.		600	IN	A	185.199.111.153
```

`dig +noall +answer www.realufo.org` (the CNAME companion):

```
www.realufo.org.	600	IN	CNAME	hectorchanht.github.io.
```

**Current TTL: 600 seconds (10 minutes) on every record.** That is
already much lower than the typical 3600 s default — Porkbun's default
TTL for new records is 600 s, and the records have evidently never been
manually tuned. The change to 300 s is a 2× reduction (small in absolute
terms) but still required for the Phase 6 cutover-gate to count from a
known-low timestamp anchor.

## Target TTL

**300 seconds (5 minutes).**

Per `.planning/research/PITFALLS.md` Pitfall #15: dropping the TTL on the
same day as the cutover means caching resolvers keep serving the OLD
(high-TTL) record for hours after the apex starts pointing at Cloudflare
Pages — producing a multi-hour split-brain where some users hit
GitHub Pages (with the kill-switch SW from plan 01-02) and others hit
Cloudflare Pages (with the new real SW). The mitigation is to drop the
TTL ≥ 7 days BEFORE cutover, so that by the time cutover happens, every
caching resolver in the chain has expired its old-TTL record at least
once and is now respecting the 300 s value.

Per `.planning/phases/01-pre-migration-safety/01-CONTEXT.md` D-17, this
seven-day window is the hard sequencing constraint on Phase 6 — the
cutover-gate reads this file's `## TTL Change Log` timestamp.

## Provider-Specific Change Procedure

> **REVISED 2026-05-25**: Path migrated from "drop TTL at Porkbun" to
> "delegate DNS Porkbun → Cloudflare, then drop TTL at Cloudflare". The
> original Porkbun-only procedure is preserved below as a fallback.

### Path A (CHOSEN) — Migrate DNS authority Porkbun → Cloudflare

CF dash: <https://dash.cloudflare.com/f1868a071996e836eae6da2b65f37929/realufo.org>

1. **At Cloudflare**: Confirm zone `realufo.org` is imported. Note the two
   assigned CF nameservers (e.g. `aaa.ns.cloudflare.com`,
   `bbb.ns.cloudflare.com` — exact pair shown on the zone Overview tab).
2. **At Cloudflare**: Verify all 5 DNS records imported correctly — 4× apex
   `A` records (185.199.108-111.153) + 1× `www` CNAME →
   `hectorchanht.github.io.`. Add any missing rows. Set proxy status to
   **DNS only** (grey cloud) initially — orange-cloud proxy can be enabled
   later once GitHub Pages → CF Pages cutover (Phase 6).
3. **At Porkbun**: <https://porkbun.com/account/login> → Domain Management
   → `realufo.org` → "Details" → "Authoritative Nameservers". Replace the 4
   Porkbun NS (`curitiba/fortaleza/maceio/salvador.ns.porkbun.com`) with
   the 2 Cloudflare NS from step 1. Save.
4. **Wait for NS propagation** (~30 min to a few hours; Porkbun's own
   parent-zone update is usually <30 min). Verify:
   ```
   dig +noall +answer NS realufo.org @1.1.1.1
   dig +noall +answer NS realufo.org @8.8.8.8
   ```
   Both should report the two `*.ns.cloudflare.com` names.
5. **At Cloudflare**: Once NS propagated, set TTL on every DNS record to
   `300` seconds (DNS tab → edit each row → change TTL from `Auto` to
   `2 minutes` or custom `300`). Auto-TTL on CF is normally 300 s for
   non-proxied records anyway, but pin explicitly to satisfy the
   `## Verification Log` evidence below.
6. **Verify** at multiple resolvers (per CONTEXT.md D-10 + 01-04 Task 2
   methodology):
   ```
   dig +noall +answer realufo.org @1.1.1.1
   dig +noall +answer realufo.org @8.8.8.8
   dig +noall +answer realufo.org @9.9.9.9
   ```
   All three should report TTL `≤ 300` and the same four A-record values.
7. **Record** the propagation-confirmed UTC timestamp in `## TTL Change Log`
   below — this anchors the 7-day Phase 6 cutover gate (NOT the NS-swap
   timestamp; the gate measures from TTL-on-Cloudflare-verified).

### Path B (FALLBACK) — Original Porkbun-DNS-only procedure

1. **Log in** to <https://porkbun.com/account/login>.
2. **Open the DNS records page** for `realufo.org`: navigate to "Domain
   Management" (left sidebar) → click `realufo.org` → click "Details" →
   click "DNS Records" (or go directly to
   <https://porkbun.com/account/domainsSpeedy>, find the row for
   `realufo.org`, and click the "DNS" icon on its right).
3. **Edit each of the four apex (`@`) A records** (one per
   `185.199.108-111.153` IP). For each row: click the pencil/edit icon →
   change the "TTL" field from `600` (current) to **`300`** (Porkbun's
   TTL field accepts seconds directly) → click "Save".
4. **Edit the `www` CNAME record** (Type=CNAME, Host=`www`,
   Answer=`hectorchanht.github.io.`). Click the pencil/edit icon →
   change TTL from `600` to **`300`** → click "Save".

Cross-checks before leaving the dashboard:

- All five records (4× apex A + 1× www CNAME) now show TTL=300 in the
  Porkbun records table.
- No A or CNAME rows for `realufo.org` were accidentally deleted.
- No new records were created.

If Porkbun's UI has changed and the TTL field is not visible inline,
Porkbun also exposes a JSON DNS API
(<https://porkbun.com/api/json/v3/documentation>) that supports
`/dns/edit/{domain}/{id}` with a `ttl` parameter — but the dashboard
edit is the recommended path for a one-time five-record change.

## TTL Change Log

_(Populated by Task 2 step 3, after the operator changes the TTL in the
Porkbun dashboard. Format: ISO-8601 UTC timestamp + one-line summary.)_

<!-- Example expected line:
- 2026-05-25T05:00:00Z — TTL on realufo.org A records (4×) and www CNAME (1×) dropped from 600 s to 300 s via Porkbun DNS dashboard.
-->

## Verification Log

_(Populated by Task 2 step 6, after the operator confirms the change via
`dig`. Format: ISO-8601 UTC timestamp + one-line dig result.)_

<!-- Example expected lines:
- 2026-05-25T07:00:00Z — dig +noall +answer realufo.org @1.1.1.1 reports TTL=300 (≤ 300).
- 2026-05-25T07:00:00Z — dig +noall +answer realufo.org @8.8.8.8 reports TTL=300 (≤ 300).
-->

## Phase 6 Cutover Countdown

Phase 6 cutover-gate reads the timestamp in `## TTL Change Log` (NOT the
`## Verification Log`). The semantics is "deploy date starts the clock",
identical to the kill-switch SW's 14-day gate from plan 01-02 (the
D-08 analog). Phase 6 may not start before:

**(TTL Change Log timestamp) + 7 days**

…with the additional cross-phase gate that `## Status` must be
`verified` (i.e. the operator has not just clicked save in the dashboard
but also confirmed via dig that the change propagated to at least 1.1.1.1
and 8.8.8.8). See `.planning/ROADMAP.md` §Phase 1 success criterion 4 +
§Cross-Phase Dependencies item 3.

Phase 6 cutover-gate verifier (when written, in Phase 6's planning)
should:

1. Parse the first ISO-8601 timestamp from `## TTL Change Log`.
2. Confirm `## Status` is `verified`.
3. Confirm `(now - timestamp) >= 7 days`.
4. Re-run `dig +noall +answer realufo.org` at gate-check time and
   confirm the live TTL is still ≤ 300 (i.e. the change wasn't reverted
   between TTL drop and cutover day).
