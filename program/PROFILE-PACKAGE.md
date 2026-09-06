# Profile package prototype 0.1

This is an experimental publication contract, not a change to existing Prim instance formats. D002 and D005 explain the decisions.

## Unit

One directory contains `PROFILE.md`: UTF-8 YAML frontmatter enclosed by `---` lines, then a nonempty Markdown body. The body explains the domain and references progressively loaded resources. Repository, directory name, and source host are not identity.

Required metadata: `format: prim-profile`, string `manifest_version: "0.1"`, `id`, `name`, `description`, explicit semantic `version`, and `maturity`. IDs use `namespace/name`, with lowercase kebab-case components up to 64 characters. Names are at most 128 characters; descriptions at most 1,024. Maturity is development, alpha, beta, stable, or deprecated, and remains publisher-declared rather than verified.

Optional metadata: `license`, `kinds`, `legacy_aliases`, `resources`, and `extensions`. Kinds/aliases are unique kebab-case strings. Aliases are informational; no cross-publisher global alias registry or automatic migration is implemented. Unknown top-level fields fail; extensibility lives under the `extensions` mapping. Values must be JSON-compatible; quote dates and versions.

Resource names are kebab-case keys mapped to canonical local POSIX relative paths. Absolute paths, URLs, schemes, backslashes, dot/traversal components, missing paths, symlinks in declared resource paths, and nonregular files are rejected. A referenced directory's contents are not recursively security-audited.

## Discovery

The local caller explicitly chooses a root. The scanner recursively looks for PROFILE.md, with depth and entry budgets, ignoring `.git`, environments, dependency directories, and caches. A discovered package is a boundary: example packages inside it are not independent publications. Multiple profiles and multiple explicit versions can share a source. Duplicate identity/version pairs fail rather than win by search order.

The output sorts by ID, version text, and relative location. This is deterministic ordering, not semantic-version resolution or a latest-version policy. The source location in the output is a relative locator, not identity. No absolute machine path or private instance data is automatically uploaded. No network operation occurs.

An unreadable portion, malformed discovered package, exceeded limit, ambiguous duplicate, or symlink in the scanned source fails the operation: no successful partial catalog. A root with no profile packages fails rather than claiming legacy folders were migrated.

## Honest verification

A successful inspection checks manifest structure and declared local resource paths. Output explicitly says profile conformance is `not_checked`, publisher identity `not_verified`, and security review `not_performed`. Referencing `validator.py` never executes it. Self-declared maturity is not a certification.

`manifest_sha256` hashes PROFILE.md bytes only. It does NOT hash resources, authenticate a publisher, establish immutable distribution, or prove factual correctness. Complete package manifests, signature verification, immutable downloads, dependency/version resolution, and supply-chain review remain open program obligations.

The reader bounds file size (64 KiB), YAML events (2,048), nesting (16), and discovery entries (10,000). Duplicate keys, aliases, anchors, merge keys, unsupported tags, non-JSON values, and malformed metadata fail. The supported execution context is a trusted, non-mutating local checkout. It is not a hardened sandbox against concurrent filesystem replacement by an adversary.

## CLI

`python tools/profile_catalog.py inspect profiles/research` inspects one package.
`python tools/profile_catalog.py discover profiles` emits the catalog.
`--output registry/profiles.generated.json` atomically writes an explicitly selected JSON view.
`--check registry/profiles.generated.json` checks deterministic regeneration.

This is reference tooling, not a published `prim profile add` command. Git/HTTP installation, production SDK integration, and website publication remain unimplemented.
