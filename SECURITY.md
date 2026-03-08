# Security Policy

## Scope

This repository is the official package index for [mojo-pkg](https://github.com/Mosaad-M/mojo-pkg).
It is the trust anchor for all package installations — a compromise here affects every
user who runs `mojo-pkg install`.

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Malicious tarball URL | Client enforces `https://github.com/` prefix; any other URL is rejected |
| Tampered tarball | SHA-256 verified client-side before unpacking; missing hash is a fatal error |
| Package name injection (path traversal / shell injection) | Client enforces `[a-z0-9][a-z0-9_-]*` name regex before using name in paths or commands |
| Version string injection | Client enforces `X.Y.Z` digits-only format |
| C dependency path traversal | Client enforces basename-only source paths (`/` and `..` rejected) |
| Malicious registry entry via PR | All changes require a PR; no direct push to `main` |
| Dependency confusion | Package names are unique; the index is the single source of truth |

## What Is NOT in Scope (Yet)

- **Cryptographic index signing** (Ed25519 per-entry signatures) — planned once a Mojo
  signing library is available.
- **Package author identity verification** — currently relies on GitHub repository
  ownership.

## Reporting a Vulnerability

If you discover a security issue in the index data or the `mojo-pkg` client:

1. **Do not open a public issue.**
2. Open a [GitHub Security Advisory](https://github.com/Mosaad-M/mojo-pkg-index/security/advisories/new)
   in this repository, or email the maintainer directly.
3. Include: a description of the issue, reproduction steps, and the potential impact.
4. Allow up to 7 days for an initial response and 30 days for a fix before public
   disclosure.

## Safe Package Submission

When submitting a new package via pull request:

- The `tarball_url` must point to a tagged GitHub release (`refs/tags/vX.Y.Z`).
- The `sha256` must be the hex-encoded SHA-256 of the tarball at that URL.
- The package name must match `[a-z0-9][a-z0-9_-]*`.
- No secrets, private keys, or credentials may appear anywhere in the JSON.

Verify your sha256 with:

```bash
curl -sL <tarball_url> | sha256sum
```
