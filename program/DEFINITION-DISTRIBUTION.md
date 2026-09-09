# Local definition publication and resolution — prototype 0.1

Requirements: PUB-002, PUB-003, PUB-004, PUB-006, DIR-002. Decision D018.
This is an installed, offline workflow in `prim-foundation-mcp` 0.1.0a2.
Permanent namespace ownership, transfers, aliases and publisher authentication
remain open under D102. A configured namespace allowlist expresses the reader's
source policy; it does not prove that a publisher owns that namespace.

## Publish independently

Use a reviewed wheel or immutable Git-source installation as described in
`services/library/README.md`. Copy `services/library/examples/external-note` into
your own folder or repository. Neither that repository nor its definitions need
to be hosted by the Foundation. The example is synthetic, not a testimonial.

```bash
prim-library publish ./external-note --output ./source-v1.json
```

This builds a local distribution file and prints its **exact-file SHA-256**.
It does not upload, crawl, execute code or publish to a package index. Transfer
the file and obtain its expected digest through your own reviewed channel.
A checksum supplied by the same untrusted download is not authentication.
Output must be new; existing distributions are never overwritten.

The installed publisher and repository builder share one safe `PROFILE.md`
parser and compiler. Only the manifest and explicitly declared UTF-8 `.md` and
`.json` resource files are copied. Declared directories remain descriptive
pointers; their contents, undeclared private records, scripts and sibling
repositories are not recursively distributed. Select and inspect your source:
an explicitly declared file can itself contain sensitive data. The manifest
resource cannot be redirected to a different file.

## Resolve selected sources

Create `request.json` beside the transferred source. Replace `SOURCE_SHA256`
with the digest from a trusted publication/transfer record:

```json
{
  "format": "prim-library-request",
  "version": 1,
  "allow_deprecated": false,
  "sources": [
    {
      "name": "my-publisher",
      "path": "source-v1.json",
      "sha256": "SOURCE_SHA256",
      "namespaces": ["example"],
      "visibility": "private"
    }
  ],
  "requirements": [{"id": "example/note", "version": "0.1.0-dev.1"}]
}
```

```bash
prim-library resolve ./request.json --output ./installation-v1
prim-library --library ./installation-v1/library.json create example/note --version 0.1.0-dev.1 --output ./my-note
prim-library --library ./installation-v1/library.json check-pack ./my-note
```

Paths are explicit local files, relative to the request file unless absolute.
There is no ambient source search, URL fetch, credentials discovery or network
fallback. Every configured source must be available and match its expected
file digest. Each definition and withdrawal must be within that source's
explicit namespace allowlist. Unknown distribution fields/versions fail.

The resulting directory contains `library.json` (the selected definitions and
transitive dependency closure), `prim-library.lock.json` (source policies and
exact resolved pins), and `sources/<sha256>.json` (complete original source
bytes, including lifecycle records). Complete sources can contain definitions
that were not selected; protect the whole cache accordingly. The portable lock
contains source labels, never original filesystem paths. Source labels are
user-selected metadata and should not contain secrets.

On POSIX systems bundle directories are mode 0700 and files 0600. If any source
is private, the bundle is marked private, even when a selected definition also
has a public mirror. This label is not encryption, an ACL service or a guarantee
that manually copied files remain private. The existing HTTP service still
requires explicit approval to serve a custom library publicly. Local stdio can
consume the resulting library without publishing it.

## Selection and dependencies

An exact root may additionally specify `definition_sha256`. A bounded root
interval uses this alternative shape (lower inclusive, upper exclusive):

```json
{"id":"example/note","minimum":"1.0.0","before":"2.0.0","allow_prerelease":false}
```

Selection uses SemVer precedence. Prereleases require explicit interval opt-in;
an exact prerelease request is already explicit. Equal-precedence versions with
different build metadata require an exact version. Deprecated definitions
require `allow_deprecated: true`, and the lock retains their maturity. No
unavailable exact version silently upgrades. Maturity remains self-declared.

Dependencies are optional namespaced manifest extensions:

```yaml
extensions:
  prim-library-dependencies:
    version: 1
    requires:
      - id: example/common
        version: 1.0.0
        definition_sha256: REPLACE_WITH_REVIEWED_DEFINITION_DIGEST
```

Dependency versions are exact. Their definition digest is optional at authoring
time (allowing ordinary dependency graph construction); every selected
transitive definition is digest-pinned in the resulting lock. All source files
are already pinned before resolution. Duplicate dependency identities, missing
pins, conflicting versions and cycles fail. Only one version per identity is
selected. Dependencies supply definitions, not merged schemas or executable
behavior; no dependency code is imported or run.

Exact roots resolve before interval roots. An interval can reuse a compatible
exact dependency pin. Otherwise it chooses its highest permitted version.
This is a deterministic bounded resolver, not a general backtracking solver:
if its chosen versions conflict, supply compatible exact roots rather than
expecting it to silently downgrade. Full IDs are required; aliases and namespace
transfers are not guessed. Identical mirrored definitions retain every source
label; different bytes for one ID/version fail regardless of source order.

## Withdrawal, updates and offline rollback

The version-1 source envelope contains `format: prim-library-source`, `version`,
a complete `library` snapshot and a `withdrawn` array. A publisher can pass
`--withdrawals ./withdrawals.json` with entries shaped as follows:

```json
[{"id":"example/note","version":"0.1.0-dev.1","definition_sha256":"DEFINITION_SHA256","reason":"Reason recorded by this source"}]
```

Withdrawal is a source assertion covered by the **source file** digest, separate
from the original definition digest. It can refer to a definition removed from
the current snapshot. Any configured source's withdrawal vetoes that exact pin,
including a copy retained by another mirror. A withdrawn ID/version cannot be
republished with different bytes to evade the tombstone. Retraction never
modifies the original definition's bytes or promises authenticated authority.

To update, publish/transfer a new source file, explicitly review its new digest
and policy, then resolve a new installation directory. Old bundles remain
intact. To reproduce an approved prior installation after the source moves or
is removed, retain its reported `lock_sha256` through a trusted channel:

```bash
prim-library restore ./installation-v1/prim-library.lock.json --cache ./installation-v1/sources --expected-sha256 LOCK_SHA256 --output ./restored-v1
```

Restore verifies the lock, reads only hash-named local cache files, repeats the
original resolution and compares the exact result. Missing or corrupt bytes
fail before publishing a destination. It cannot discover subsequent online
withdrawals or newly compromised publishers while offline. Restoring history
is not a claim that it remains safe or currently endorsed. Check current
approved source policy before adopting an old installation for new work.

## Bounds and proof

Limits: 16 sources; 128 definitions per source and combined; 128 roots,
dependencies and withdrawals; 32 dependency levels; 128-character versions;
512 KiB per resource/lock/request; 8 MiB per full library; source envelope at
most 8.5 MiB. Existing bounded JSON, schema and YAML readers apply. Symlinks,
nonregular input files and output replacement are rejected. These filesystem
operations assume a trusted, non-mutating local tree; they are not a sandbox
against a hostile process racing ancestor directories or physical power loss.

Tests exercise actual external files, dependency graphs, collisions, version
intervals, lifecycle decisions, integrity failures, private cache permissions,
source deletion/moves and exact offline replay. The clean-wheel smoke invokes
the installed console entrypoint outside the checkout to publish a synthetic
external profile, resolve it, delete its source, restore, create and check a
record. This is not an actual independent publisher trial, security review,
remote authenticated registry, stable release or namespace governance decision.
