# Security policy

realufo.org is a **static archive** of public-domain government UAP records.
There is no backend, no user authentication, no database, no paid third-party
service. The whole site is served as static files from GitHub Pages.

## What we care about

Please report any of the following:

- Cross-site scripting (XSS), URL injection, or HTML smuggling in the
  search / timeline / map / archive pages.
- **Source-URL integrity** — if a manifest entry points to a domain that no
  longer belongs to the government source (i.e. an expired or hijacked URL).
- Service-worker cache poisoning, manifest tampering, or other PWA issues.
- Anything that could mislead a visitor about the authenticity of a record.

## What we don't care about (will close as not applicable)

- Findings against `vercel.io`, `*.vercel.app`, `*.amazonaws.com` — we do not
  use these services. realufo.org is hosted on GitHub Pages.
- "Missing Content-Security-Policy header" without a demonstrated exploit.
- Self-XSS that requires the user to paste code into their own console.
- Reports against the public domain content itself.

## How to report

Three channels, in order of preference:

1. **GitHub Security Advisories** — open a private advisory at
   <https://github.com/hectorchanht/war-gov-ufo-release/security/advisories/new>
2. **Email** — `security@realufo.org` (PGP key on request).
3. **Public issue** — only for low-impact findings where there is no
   exploitable consequence to current visitors.

## Disclosure window

We ask for **30 days** to investigate and patch before public disclosure.
We will credit you in `Acknowledgments` if you wish.
