#!/usr/bin/env bash
# Verify the SHA-256 of a published tarball before submitting a PR.
#
# Usage:
#   ./scripts/verify_sha256.sh <tarball_url> <expected_sha256>
#
# Example:
#   ./scripts/verify_sha256.sh \
#     https://github.com/Mosaad-M/json/archive/refs/tags/v1.0.0.tar.gz \
#     0f55f19772c5a7649f85146053400e0d08321220115e2dc93d76b82b372f11df

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: $0 <tarball_url> <expected_sha256>" >&2
    exit 1
fi

url="$1"
expected="$2"
actual=$(curl -sL "$url" | sha256sum | awk '{print $1}')

if [ "$actual" = "$expected" ]; then
    echo "OK: sha256 matches"
    echo "  $actual"
else
    echo "FAIL: sha256 mismatch" >&2
    echo "  expected: $expected" >&2
    echo "  actual:   $actual" >&2
    exit 1
fi
