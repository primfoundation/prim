# Threat model — local Research compatibility slice

Status: scoped engineering model; not an independent security audit. SEC-001 and
SEC-003 remain open for the wider Foundation platform.

## Assets and authority

Preserve original local records, private attachments, exact historical semantics,
review honesty, and the user's filesystem. Record contents, file names, metadata,
citations and even approval labels are untrusted data. A record never grants
execution rights. No credentials or private instances go to a public registry.
The legacy oracle is reviewed repository code, pinned and hash-checked; the
research pack cannot supply or select arbitrary executable validation code.

## Implemented boundaries and tests

| Threat | Control in this slice |
| --- | --- |
| Relative path traversal, absolute paths, drive paths and backslashes | Canonical portable paths; reject `..`, reserved names and invalid components before writes. |
| Case or Unicode normalization collisions | Reject ambiguous paths rather than overwriting one file with another. |
| Symlinks and FIFOs/device files | Reject roots/ancestors, entries and special files; no-follow/nonblocking file opens where available. |
| Parser/memory exhaustion | File, total-byte, entry-count, path-depth, JSON-byte, Markdown-size and YAML event/depth limits. |
| Duplicate JSON/YAML keys, YAML aliases/tags/merge keys | Reject ambiguous transport; preserve original documents but report unparsed/disagreeing interpretations. |
| Hostile Python or validators included as evidence | Never import input code; only use the fixed local baseline engine. |
| False confidence from an old validator | Explicit legacy result, review warnings and not-checked truth/identity/authority dimensions. |
| Silent metadata/unknown-field loss | Preserve every bounded file's bytes; retain binary data and empty directories; publish transport limits. |
| Overwriting originals | New destinations only; refuse outputs nested inside a source pack. |
| HTML/script injection and remote-image tracking | Escape all source text; script-free view; restrictive CSP; no source retrieval. |
| Digest substitution | Verify file and aggregate digests, but never treat a self-consistent bundle as authenticated. |

## Resource envelope

At most 1,024 files, 2,048 total entries, 16 directory levels, 4 MiB per file,
16 MiB total raw bytes and 24 MiB preservation JSON. Markdown above 256 KiB is
preserved but not sent to the legacy parser. Safe metadata comparison permits
at most 2,048 YAML events and 16 nested mappings/sequences. Limits are implementation
bounds, not Prim-wide semantic rules. Exceeding a preservation bound fails rather
than emitting a successful partial copy.

## Explicitly outside this assurance

The supported filesystem is trusted and non-mutating during a command. Ancestor
symlink checks and rename rechecks are not a hardened defense against an attacker
concurrently replacing directories; native descriptor-relative sandboxing is
future work. Restore does not promise crash consistency or OS-metadata fidelity.
Output views can contain sensitive data and must be shared only intentionally.

ZIP/TAR import, remote resolution, encrypted transport, keys, publisher signatures,
process isolation against a compromised dependency, hostile rendered plugins,
full prompt-injection defense for downstream agents, and production operation
are not implemented here. A restrictive HTML view is not a complete browser
sandbox. Embedded content must remain data to agents; this tool cannot guarantee
that an external agent will ignore malicious natural-language instructions.

The baseline engine has known permissive and erroring behaviors. It runs on a
bounded frozen copy, but its result is not upgraded into factual, security or
Research vNext certification. Authentication and authorization remain explicit
separate open gates. Do not make public safety claims from these unit tests.
