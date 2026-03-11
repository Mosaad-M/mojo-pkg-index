#!/usr/bin/env python3
"""Validate all package entries in the mojo-pkg-index.

Checks performed for each packages/<name>.json:
  - name matches ^[a-z0-9][a-z0-9_-]{0,63}$
  - every version.tarball_url starts with https://github.com/
  - every version.sha256 is 64 lowercase hex chars (non-empty)
  - every version.version matches ^\d+\.\d+\.\d+$
  - all names in version.deps[] exist in index.json
  - no circular dependencies (DFS across the dep graph)
"""

import json
import os
import re
import sys

NAME_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,63}$')
VERSION_RE = re.compile(r'^\d+\.\d+\.\d+$')
SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
URL_PREFIX = 'https://github.com/'

errors = []

# ── Load index.json ────────────────────────────────────────────────────────────
index_path = 'index.json'
if not os.path.exists(index_path):
    print(f"FAILED: {index_path} not found")
    sys.exit(1)

with open(index_path) as f:
    try:
        index = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAILED: {index_path}: invalid JSON: {e}")
        sys.exit(1)

known_packages = set(index.get('packages', []))

# ── Validate each package file ─────────────────────────────────────────────────
dep_graph: dict[str, list[str]] = {}

for pkg_name in sorted(known_packages):
    path = f'packages/{pkg_name}.json'
    if not os.path.exists(path):
        errors.append(f"{path}: file not found")
        dep_graph[pkg_name] = []
        continue

    with open(path) as f:
        try:
            pkg = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{path}: invalid JSON: {e}")
            dep_graph[pkg_name] = []
            continue

    # name
    name = pkg.get('name', '')
    if not NAME_RE.match(name):
        errors.append(
            f"{path}: name '{name}' does not match ^[a-z0-9][a-z0-9_-]{{0,63}}$"
        )
    if name != pkg_name:
        errors.append(
            f"{path}: name '{name}' does not match filename '{pkg_name}'"
        )

    # versions
    versions = pkg.get('versions', [])
    if not versions:
        errors.append(f"{path}: no versions defined")

    latest_deps: list[str] = []
    for v in versions:
        ver = v.get('version', '')
        if not VERSION_RE.match(ver):
            errors.append(
                f"{path}: version '{ver}' does not match ^\\d+\\.\\d+\\.\\d+$"
            )

        tarball_url = v.get('tarball_url', '')
        if not tarball_url.startswith(URL_PREFIX):
            errors.append(
                f"{path}: tarball_url '{tarball_url}' must start with {URL_PREFIX}"
            )

        sha256 = v.get('sha256', '')
        if not SHA256_RE.match(sha256):
            errors.append(
                f"{path}: sha256 '{sha256}' must be 64 lowercase hex chars"
            )

        deps = v.get('deps', [])
        if not isinstance(deps, list):
            errors.append(f"{path}: 'deps' must be an array")
        else:
            for dep in deps:
                if not NAME_RE.match(dep):
                    errors.append(
                        f"{path}: dep name '{dep}' does not match ^[a-z0-9][a-z0-9_-]{{0,63}}$"
                    )
                elif dep not in known_packages:
                    errors.append(
                        f"{path}: dep '{dep}' is not listed in index.json"
                    )
        latest_deps = deps  # use deps from the last version for cycle check

    dep_graph[pkg_name] = latest_deps

# ── Circular dependency check (DFS) ───────────────────────────────────────────
def find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    visited: set[str] = set()
    path: list[str] = []
    path_set: set[str] = set()

    def dfs(node: str) -> bool:
        if node in path_set:
            return True
        if node in visited:
            return False
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True
        path.pop()
        path_set.discard(node)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return list(path)
    return None

cycle = find_cycle(dep_graph)
if cycle:
    errors.append(f"circular dependency detected: {' -> '.join(cycle)}")

# ── Report ─────────────────────────────────────────────────────────────────────
if errors:
    print(f"FAILED: {len(errors)} error(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"OK: all {len(known_packages)} package(s) validated successfully")
