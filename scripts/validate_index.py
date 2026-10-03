#!/usr/bin/env python3
r"""Validate all package entries in the mojo-pkg-index.

Checks performed for each packages/<name>.json:
  - name matches ^[a-z0-9][a-z0-9_-]{0,63}$
  - every version.tarball_url starts with https://github.com/
  - every version.sha256 is 64 lowercase hex chars (non-empty)
  - every version.version matches ^\d+\.\d+\.\d+$
  - all names in version.deps[] exist in index.json
  - optional version.dep_constraints is an object whose keys are in deps[]
    and whose values are constraints like ">=1.0.0,<2.0.0" (mojo-pkg >= 0.7.0)
  - no circular dependencies (DFS across the dep graph)
  - packages/all.json (read first by mojo-pkg) matches every
    packages/<name>.json exactly
"""

import json
import os
import re
import sys

NAME_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,63}$')
VERSION_RE = re.compile(r'^\d+\.\d+\.\d+$')
SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
# One or more comparators joined by commas (all must hold); explicit operator
COMPARATOR = r'\s*(>=|<=|>|<|=|\^)\d+\.\d+\.\d+\s*'
CONSTRAINT_RE = re.compile(rf'^{COMPARATOR}(,{COMPARATOR})*$')
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
        constraints = v.get('dep_constraints', {})
        if not isinstance(constraints, dict):
            errors.append(f"{path}: version {ver}: 'dep_constraints' must be an object")
        else:
            for dep, constraint in constraints.items():
                if not isinstance(deps, list) or dep not in deps:
                    errors.append(
                        f"{path}: version {ver}: dep_constraints key '{dep}' is not in deps"
                    )
                if not isinstance(constraint, str) or not CONSTRAINT_RE.match(constraint):
                    errors.append(
                        f"{path}: version {ver}: dep_constraints['{dep}'] = {constraint!r} "
                        "is not a constraint like '>=1.0.0' or '>=1.0.0,<2.0.0'"
                    )
        latest_deps = deps  # use deps from the last version for cycle check

    dep_graph[pkg_name] = latest_deps

# ── all.json must mirror the per-package files (mojo-pkg reads it first) ──────
all_path = 'packages/all.json'
try:
    all_pkgs = {p.get('name'): p for p in json.load(open(all_path)).get('packages', [])}
except (OSError, json.JSONDecodeError) as e:
    errors.append(f"{all_path}: cannot read: {e}")
    all_pkgs = None
if all_pkgs is not None:
    if set(all_pkgs) != known_packages:
        errors.append(
            f"{all_path}: package set {sorted(all_pkgs)} != index.json {sorted(known_packages)}"
        )
    for pkg_name in sorted(known_packages & set(all_pkgs)):
        try:
            single = json.load(open(f'packages/{pkg_name}.json'))
        except (OSError, json.JSONDecodeError):
            continue  # already reported above
        if single != all_pkgs[pkg_name]:
            errors.append(
                f"{all_path}: entry for '{pkg_name}' differs from packages/{pkg_name}.json"
            )

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
