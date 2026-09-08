# Offline host contract — experimental version 1

Requirements: PUB-001/PUB-002/PUB-004, DEV-001/DEV-004, HUM-001/HUM-004,
INTEROP-001/INTEROP-004 and RELENG-001/RELENG-002/RELENG-003.

A host consumes a data-only `prim-host-catalog` containing creation kits from the
verified Foundation Library. Each kit retains its full publisher-qualified profile
ID, explicit version and complete definition SHA-256. Repository paths and source
locations are provenance, not identity. Two source locations with the same pinned
definition describe the same definition; a changed hash never silently replaces it.

The catalog itself must be supplied with an expected SHA-256 through a trusted
installation or explicit local import. A matching checksum pins bytes. It does
not authenticate the publisher, approve the definition, confer authority or make
its statements true. The bundled catalog records the exact Foundation source
commit for its four existing development definitions. This does not promote them
to stable standards or close D102/D106.

`prim-library export-host` emits a portable catalog. The TypeScript SDK's
`ProfileLibrary` and Primboard's native Swift host independently interpret its
schema and recorded-reference rules. No profile JavaScript, Swift, Python,
validator command, remote `$ref`, network fetch or agent is executed. Unsupported
assertions or rules prevent loading; they do not produce partial passing checks.
Native and SDK hosts support an intentionally bounded JSON Schema vocabulary:
type, const, enum, properties, required, additionalProperties, items, length/item
bounds, numeric limits, allOf/anyOf/oneOf/not and if/then/else. Reference checks cover
unique IDs, identifier tokens, root/collection references and declared required
links. New profiles using these features require data publication, not a bespoke
host component.

Hosts preserve unknown record fields. JSON inputs reject duplicate keys, nonfinite
numbers, nesting beyond 24 and containers larger than 2,048 entries. Records are
limited to 512 KiB. Native/JavaScript numeric magnitude is bounded by 2^53−1;
applications needing larger or exact decimal values must represent them explicitly
as strings under an appropriate profile. The Swift host conservatively rejects
canonically equivalent Unicode key spellings; it does not silently merge them.

## Local records and interoperability

An exported directory contains the exact kit's authority file, a
`prim-definition.lock.json`, `index.md` and `log.md`. Import uses the full pin;
an absent version or mismatched hash fails without an upgrade. The authority file
contains the record. The face and log are views/provenance, not another authority.
Export requires a new destination beneath an explicitly selected trusted parent.
Private directories/files use 0700/0600. Exported files are unencrypted, so the
native export dialog names that consequence. Private data is never sent to the
public Library.

The supported file operations assume a trusted, non-mutating local filesystem;
this is not a sandbox against a process that can concurrently replace parent
directories. Symlinked record files and arbitrary symlinked parents are rejected.
macOS's OS-owned `/var` and `/tmp` aliases are normalized in the native host.
The record import is not a general-purpose archive or attachment migration.
Original source directories remain intact.

The shared 83-case synthetic corpus exercises all four profiles, missing fields,
wrong types, extensions, conditional Research/Decision states, dangling links,
unsupported claims and workbook number distinctions. Python, TypeScript and Swift
results are recorded separately. Actual Python-to-SDK and SDK-to-Python pack
round trips complement those cases. These are independently written software
implementations under one development effort, not independent organizational
review, real-person usability acceptance or factual validation.

## SDK distribution

The development SDK is `@eidos-agi/prim` **0.5.0-dev.2**. Its package contains
compiled JavaScript, declarations and the legacy category registry. The existing
category interfaces remain available; full profile pins are an additive interface
and do not reinterpret old category `repo` values or legacy Prim files.

The SDK workflow builds a tarball, installs it offline outside the checkout,
executes its public API/CLI and type-checks an actual consumer. CI retains the
tarball and its checksum report. A CI artifact is not an npm-index publication,
stable release or permanent distribution service.

Version 0.5.0-dev.2 checks the actual formatted authority-file bytes before export, so a successful write stays within its own reader budget. The earlier 0.5.0-dev.1 artifact remains historical.
