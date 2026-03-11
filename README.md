# mojo-pkg-index

The official package index for [mojo-pkg](https://github.com/Mosaad-M/mojo-pkg) — a Mojo-native package manager.

## Available Packages

| Package | Description | Version |
|---------|-------------|---------|
| [json](https://github.com/Mosaad-M/json) | Pure Mojo JSON parser | 1.0.0 |
| [url](https://github.com/Mosaad-M/url) | Pure Mojo URL parser | 1.0.0 |
| [tcp](https://github.com/Mosaad-M/tcp) | Pure Mojo TCP socket layer | 1.0.0 |
| [tls](https://github.com/Mosaad-M/tls) | Pure Mojo TLS 1.3 + 1.2 client | 1.0.0 |
| [requests](https://github.com/Mosaad-M/requests) | Pure Mojo HTTP/HTTPS client | 1.0.0 |

## Index Structure

```
index.json              # List of all package names
packages/
  json.json             # Metadata for each package
  url.json
  tcp.json
  tls.json
  requests.json
```

## Package Metadata Format

```json
{
  "name": "json",
  "git_url": "Mosaad-M/json",
  "description": "Pure-Mojo JSON parser and serializer",
  "license": "MIT",
  "homepage": "https://github.com/Mosaad-M/json",
  "versions": [
    {
      "version": "1.0.0",
      "published_at": "2026-03-07",
      "tarball_url": "https://github.com/Mosaad-M/json/archive/refs/tags/v1.0.0.tar.gz",
      "sha256": "0f55f19772c5a7649f85146053400e0d08321220115e2dc93d76b82b372f11df",
      "mojo_requires": ">=0.26.1",
      "deps": []
    }
  ]
}
```

## Security Model

This index is the trust anchor for all `mojo-pkg install` operations. The following
constraints are enforced both in this repository and in the `mojo-pkg` client:

- **SHA-256 integrity** — every version entry must include a non-empty `sha256` of the
  tarball. The client refuses to install a package with a missing or mismatched hash.
- **HTTPS-only tarball URLs** — all `tarball_url` values must start with
  `https://github.com/`. The client rejects any other prefix.
- **Package name restrictions** — names must match `[a-z0-9][a-z0-9_-]*` (max 64 chars).
  No path separators, shell metacharacters, or uppercase letters are allowed.
- **Version format** — versions must be `X.Y.Z` with digits only.
- **PR-required additions** — no package can be added or modified without an open pull
  request; direct pushes to `main` are blocked by branch protection.
- **No secrets in this repo** — do not commit private keys, tokens, or credentials.

Report vulnerabilities via [SECURITY.md](SECURITY.md).

## Usage

Install a package using `mojo-pkg`:

```bash
# In your project's mojoproject.toml:
# [dependencies]
# json = { git = "Mosaad-M/json", version = ">=1.0.0" }

mojo-pkg install
```

## Submitting a Package

To add a package to the index, open a pull request adding a JSON file under `packages/`.

## License

MIT — see [LICENSE](LICENSE)
