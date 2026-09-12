# Complete-pack transport, development version 1

Library 0.1.0a4 and TypeScript SDK 0.5.0-dev.3 can transfer an entire local
Prim folder through a deterministic ZIP envelope. Original attachments,
capture receipts, definition locks, logs and unknown files retain their exact
bytes. A captured Research record with a missing or changed referenced artifact
cannot be exported successfully.

```sh
prim-library export-pack ./captured-research --output ./research.prim.zip
prim-library check-transfer ./research.prim.zip --expected-sha256 ARCHIVE_SHA256
prim-library import-pack ./research.prim.zip --output ./restored-research \
  --expected-sha256 ARCHIVE_SHA256
prim-library check-pack ./restored-research
```

Use the `archive_sha256` printed by export when it is retained through a trusted
channel. `check-capture` accepts the separately retained original capture receipt
digest. Transfer integrity and initial capture verification answer different
questions: legitimate later record edits need not match the initial receipt.

The equivalent installed SDK commands are `prim profile export-pack`,
`prim profile check-transfer` and `prim profile import-pack`, with the same
arguments. Node exports `exportCompletePack`, `checkCompletePack` and
`importCompletePack`. Browser-compatible `encodeCompletePack` and
`decodeCompletePack` operate on a `Map<string, Uint8Array>` without filesystem,
network or process access. Standard Web Crypto supplies SHA-256.

## Envelope and compatibility

The ordinary ZIP STORE archive contains every regular payload file plus
`prim-transfer.json`. That reserved manifest has format `prim-complete-pack`,
version `1`, an exact three-field definition pin, and sorted file entries with
`path`, `bytes` and `sha256`. Its representation is sorted-key compact ASCII JSON
with one final newline. Payload bytes are never parsed and rewritten by transport.
The manifest precedes lexically sorted payload paths in deterministic exports.

Headers use UTF-8 filename flag `0x0800`, method 0, version-needed 20,
Unix creator `0x0314`, date 1980-01-01, regular-file mode 0600, matching CRC32,
contiguous local records and a matching single central directory. Encryption,
compression, ZIP64, extra fields, comments, links, overlapping records and trailing
data are unsupported and fail before extraction. Native command-line ZIP tools
can inspect these archives. Arbitrary ZIPs are not automatically supported.

Import verifies the entire inventory before writing private staged files and
publishes to a new directory. It restores the payload, excluding the synthetic
transport manifest; retain the archive/digest as the transfer receipt. Existing
destinations are refused. Export likewise creates a new archive, outside the
source tree. No file is executed, remotely fetched or automatically unpacked.

`index.md` and `prim-definition.lock.json` are mandatory. For known Research,
`research.json` and every declared embedded artifact must agree in path, byte
count and SHA-256. Unknown profile files are transported as opaque bytes;
this does not establish that their external references are self-contained or
that their schemas pass. Run the pinned profile validator separately.

| Bound | Development transport |
| --- | --- |
| Payload files | 256 |
| Directory count in a source folder | 256 |
| Individual file | 16 MiB |
| Sum of payload bytes | 32 MiB |
| Archive | 34 MiB |
| Path | 240 ASCII characters; at most eight segments, each at most 120 |
| Segment | Starts with a letter/digit; then letters, digits, dot, underscore or hyphen |

Absolute/traversing paths, backslashes, Windows device names, trailing dots,
case collisions and file/directory prefix collisions fail. Unsupported names
are never renamed silently. This first format intentionally rejects Unicode
filenames. Filesystem permissions become private defaults; empty directories,
timestamps, ACLs, extended attributes and executable bits are not transported.

## Source and trust boundaries

Choose a trusted local parent and pause source writers before export. Regular
file identity, size and timestamps are checked around reads, but there is no
cross-process transaction or guarantee of a coherent snapshot while another
application edits several files. The filesystem adapters are not designed for
a hostile process concurrently replacing their parent directories. Use an
application snapshot or a quiescent copied folder in that situation.

An unsigned manifest detects corruption; an attacker can rewrite an entire
archive and its manifest. A digest from an independently trusted channel pins
those bytes. Neither result authenticates a publisher, grants sharing rights,
checks factual accuracy, decrypts attachments or executes profile code. Exported
archives are local and unencrypted, including any files already in the folder.
The API reports `source_authentication: not_verified` explicitly.

`ProfileLibrary.writePack` and record-only JSON downloads create records, rather
than copying an existing complete folder. Use complete-pack transport whenever
the original folder includes additional files. Host adoption is tracked under
D95-04; standalone Library/SDK support does not close Hub or native acceptance.

## Verification

The Python suite exercises source deletion, retained capture receipts, binary
and unknown files, all four known profiles, unsafe names, symlinks/FIFOs, quotas,
corruption, malicious ZIP metadata, exclusive publication and failure cleanup.
It exports an actual Python archive, imports it through the TypeScript module,
exports byte-identical TypeScript bytes, and imports/checks the result in Python.
SDK tests additionally cover mutation of caller input during asynchronous hashing.

Actual wheel and tarball installation tests run outside the source checkout,
delete source folders before import and verify embedded original bytes through
the installed CLI/API. Release CI retains packages and reports. These checks do
not substitute for independent review or real-user acceptance across products.
