# prim (TypeScript)

Category-level Prim SDK. Node stdlib + `zip` / `unzip` / `tar`. No npm runtime deps.

This is the Prim kernel for **OKF-shaped** packs. Profiles register a validator and a view on top. They do not re-parse archives or faces. A Prim does not have to be OKF; this SDK implements the pack grammar that many current profiles use.

## Use

```ts
import { openPrim } from "@eidos-agi/prim";

const p = openPrim("house.opff.prim");
p.title; // 'Harbor House'
p.pair(); // { surface: opff-editor, … }
p.jsonl("accounts.jsonl");
p.files(); // pack-relative paths
p.close(); // drop extracted zip tmp

const mem = openPrim({ files: { "index.md": face, "log.md": log } });
```

```bash
node --experimental-strip-types sdk/typescript/src/cli.ts open <pack>
node --experimental-strip-types sdk/typescript/src/cli.ts tools <pack>
node --experimental-strip-types sdk/typescript/src/cli.ts validate <pack>
node --experimental-strip-types sdk/typescript/src/cli.ts registry
node --experimental-strip-types sdk/typescript/tests/pack.test.ts
```

## API

| Call | Does |
|---|---|
| `openPrim(source)` | Directory, `.prim.zip` / `.prim.tar.gz`, or `{ files }` map |
| `Pack.face` / `Pack.title` | Parsed `index.md` frontmatter |
| `Pack.viewKey` | `profile/subtype` or `profile/type` |
| `Pack.pair()` / `tools()` / `surface()` / `connector()` | Registry pairing. Harbor House → `opff-editor` (as `ledger`). |
| `Pack.files()` / `read` / `jsonl` | Pack-relative paths. `read` refuses `..`. |
| `Pack.close()` | Delete extracted / materialized tmp |
| `Pack.validate()` | Category gates + registered profile validator |
| `Pack.validateBase()` | Shared SPEC §4 gates only |
| `registerView` / `resolveView` | Prim UI dispatch (`ui` — how a Prim opens) |
| `registerValidator` / `validate` | Profile validators plug in here |
| `PRIMITIVES` / `primitive(name)` | The nine category primitives |
| `createTool` / `TOOL_KINDS` | Prim Tools: `surface` or `connector`; `emit` / `talk` / `receive`. Optional `as` / `bin` / `repo`. Not a tenth primitive. |
| `listTypes` / `listTools` / `listApplets` / `registerType` / `registerTool` / `registerApplet` | Category registry. Types are prim kinds. Tools cite a type (`surface` or `connector`). Applets compose types; they are not a tool kind. |

`validateBase()` checks `okf_version` / `profile` / `type`, recommends `log.md`, resolves face path pointers, checks `compose:` targets, and rejects secret-shaped strings.
# Pinned offline profiles

The development package now builds compiled JavaScript and declarations, with its
registry included. Node 22.16 or later is the tested release baseline. Build and
exercise an actual tarball installation with:

```bash
npm ci --ignore-scripts
npm run typecheck
node scripts/installed-smoke.mjs
```

The additive profile API creates and validates local records without fetching or
executing profile code:

```ts
import { ProfileLibrary } from '@eidos-agi/prim';
const library = new ProfileLibrary();
const kit = library.list().find(k => k.profile_id === 'primfoundation/person')!;
const pin = library.pin(kit);
const record = library.create(pin, {name: 'Example person'});
library.writePack(pin, record, './new-person.prim');
const reopened = library.readPack('./new-person.prim');
```

`prim profile list`, `prim profile create … --version … --output …` and
`prim profile check <folder>` expose the same behavior. Exported files are local
and unencrypted. Validation checks structure and declared references, not facts or
authority. Exact definition pins are required; a missing version never upgrades
silently. [Host contract](../../program/OFFLINE-HOST-CONTRACT.md).

For an existing folder with attachments, use `await exportCompletePack(source,
newArchive)` and `await importCompletePack(archive, newFolder, expectedSHA256)`.
The installed `prim profile export-pack`, `import-pack` and `check-transfer`
commands expose the same bounded, byte-preserving transport. It retains unknown
files and capture receipts and rejects missing Research artifacts. Browser hosts
can use the filesystem-free `encodeCompletePack`/`decodeCompletePack` functions.
[Transport contract and limits](../../program/COMPLETE-PACK-TRANSFER.md).
