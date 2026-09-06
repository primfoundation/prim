import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  FACE_VIEW,
  PRIMITIVE_NAMES,
  PrimError,
  TOOL_DIRECTIONS,
  TOOL_KINDS,
  counterpartOf,
  createTool,
  createValidator,
  createView,
  openPrim,
  parse,
  primitive,
  registerValidator,
  registerView,
  resolveView,
  trustTier,
  validate,
  viewKey,
} from "../src/index.ts";

const FACE = `---
okf_version: "0.2"
profile: ocsf
type: entity_structure
title: "Fictional Holdings"
tags: []
source:
  authority: human
  note: "invented"
---

Body text.
`;

function build(tmp: string): string {
  const pack = join(tmp, "fictional");
  mkdirSync(pack);
  writeFileSync(join(pack, "index.md"), FACE, "utf8");
  writeFileSync(join(pack, "log.md"), "# Log\n\n- created\n", "utf8");
  return pack;
}

const tmp = mkdtempSync(join(tmpdir(), "prim-ts-"));
const packDir = build(tmp);

const face = parse(FACE);
assert.equal(face.okf_version, "0.2");
assert.equal(face.profile, "ocsf");
assert.equal(face.title, "Fictional Holdings");
assert.deepEqual(face.tags, []);
assert.equal((face.source as { authority: string }).authority, "human");

const p = openPrim(packDir);
assert.equal(p.profile, "ocsf");
assert.equal(p.type, "entity_structure");
assert.equal(p.viewKey, "ocsf/entity_structure");
assert.equal(p.trust(), "human");
assert.ok(p.logFile());
assert.deepEqual(p.authorityPaths(), []);
assert.deepEqual(p.validateBase(), []);
assert.deepEqual(p.validate(), []);

for (const ext of [".prim.zip", ".prim.tar.gz"]) {
  const out = p.write(join(tmp, `fictional${ext}`));
  const back = openPrim(out);
  assert.deepEqual(back.face, p.face, ext);
  assert.deepEqual(back.validateBase(), [], ext);
  const names = new Set(back.files());
  assert.ok(names.has("index.md"), ext);
  back.close();
}

const broken = join(tmp, "broken");
mkdirSync(broken);
writeFileSync(join(broken, "index.md"), "---\nprofile: ocsf\n---\n", "utf8");
const problems = openPrim(broken).validateBase();
assert.ok(problems.some((x) => x.includes("okf_version")), problems.join("\n"));
assert.ok(problems.some((x) => x.includes("log.md")), problems.join("\n"));

const leaky = join(tmp, "leaky");
mkdirSync(leaky);
writeFileSync(join(leaky, "index.md"), FACE, "utf8");
writeFileSync(join(leaky, "log.md"), "api_key: sk-abcdefghijklmnopqrstuvwxyz01\n", "utf8");
assert.ok(openPrim(leaky).validateBase().some((x) => x.includes("secret")));

const pointed = join(tmp, "pointed");
mkdirSync(pointed);
writeFileSync(
  join(pointed, "index.md"),
  FACE.replace('note: "invented"', 'note: "invented"\nbook: book.json'),
  "utf8",
);
writeFileSync(join(pointed, "log.md"), "# Log\n", "utf8");
const missingBook = openPrim(pointed).validateBase();
assert.ok(missingBook.some((x) => x.includes("book.json")), missingBook.join("\n"));
writeFileSync(join(pointed, "book.json"), "{}", "utf8");
const pointedPack = openPrim(pointed);
assert.deepEqual(pointedPack.validateBase(), []);
assert.deepEqual(pointedPack.authorityPaths(), ["book.json"]);
assert.deepEqual(pointedPack.constraintPaths(), []);
mkdirSync(join(pointed, "bible"));
writeFileSync(join(pointed, "bible", "canon.json"), "{}", "utf8");
const pointed2 = openPrim(pointed);
assert.ok(pointed2.constraintPaths().includes("bible"));
assert.deepEqual(pointed2.authorityPaths(), ["book.json"]);

p.appendLog("sdk wrote a line", "2026-08-19");
assert.ok(p.read("log.md").includes("2026-08-19 — sdk wrote a line"));
assert.ok(p.readBytes("index.md").subarray(0, 3).equals(Buffer.from("---")));

const composed = join(tmp, "composed");
mkdirSync(composed);
writeFileSync(
  join(composed, "index.md"),
  FACE.replace("tags: []", "compose:\n  - orf:example\n  - neighbor"),
  "utf8",
);
writeFileSync(join(composed, "log.md"), "# Log\n", "utf8");
const composeProblems = openPrim(composed).validateBase();
assert.ok(composeProblems.some((x) => x.includes("neighbor")), composeProblems.join("\n"));
assert.ok(!composeProblems.some((x) => x.includes("orf:example")));

assert.deepEqual(PRIMITIVE_NAMES, [
  "file",
  "face",
  "authority",
  "constraint",
  "log",
  "validator",
  "ui",
  "compose",
  "trust",
]);
assert.ok(primitive("ui").notThis.startsWith("A fixed application"));
assert.ok(!PRIMITIVE_NAMES.includes("tool"));
assert.ok(!PRIMITIVE_NAMES.includes("surface"));
assert.ok(!PRIMITIVE_NAMES.includes("connector"));
assert.deepEqual([...TOOL_KINDS], ["surface", "connector"]);
assert.deepEqual([...TOOL_DIRECTIONS], ["emit", "talk", "receive"]);
assert.equal(counterpartOf("surface"), "human");
assert.equal(counterpartOf("connector"), "system");
const surface = createTool({
  name: "cerebro-print",
  kind: "surface",
  direction: "emit",
  cites: "obf:metrics-gold-fairy-tale",
});
assert.equal(surface.kind, "surface");
assert.equal(counterpartOf(surface.kind), "human");
const ledger = createTool({
  name: "opff-editor",
  kind: "surface",
  direction: "talk",
  cites: "opff",
  as: "ledger",
  repo: "eidos-agi/prim.opff",
});
assert.equal(ledger.as, "ledger");
assert.equal(ledger.repo, "eidos-agi/prim.opff");

const house = join(tmp, "harbor");
mkdirSync(house);
writeFileSync(
  join(house, "index.md"),
  `---
okf_version: "0.2"
profile: opff
type: household
title: Harbor House
plane: personal
---

Fictional ledger.
`,
  "utf8",
);
writeFileSync(join(house, "log.md"), "# Log\n\n- created\n", "utf8");
const hp = openPrim(house);
assert.equal(hp.profile, "opff");
assert.equal(hp.title, "Harbor House");
assert.equal(hp.surface()?.name, "opff-editor");
assert.equal(hp.surface({ as: "ledger" })?.as, "ledger");
assert.equal(hp.surface({ as: "editor" }), undefined);
assert.equal(hp.surface({ as: "viewer" })?.name, "prim-viewer");
assert.equal(hp.connector()?.name, "prim-viewer-webmcp");
assert.equal(hp.connector({ as: "webmcp" })?.name, "prim-viewer-webmcp");
// The registry also publishes two category-wide hosts. They cite every profile;
// they must remain discoverable without displacing the profile-specific editor.
assert.deepEqual(hp.tools().map((t) => t.name), [
  "opff-editor", "prim-viewer", "prim-viewer-webmcp", "prim-mac", "prim-web",
]);
assert.deepEqual(hp.tools({ kind: "surface", as: "host" }).map((t) => t.name), [
  "prim-mac", "prim-web",
]);
assert.deepEqual(hp.tools({ kind: "connector", as: "host" }), []);
assert.equal(hp.pair().surface?.name, "opff-editor");
assert.equal(hp.pair().connector?.name, "prim-viewer-webmcp");
assert.deepEqual(p.tools().map((t) => t.name), [
  "ocsf-editor", "prim-viewer", "prim-viewer-webmcp", "prim-mac", "prim-web",
]);
assert.ok(hp.files().includes("index.md"));
assert.ok(hp.files("**/*.md").includes("log.md"));
assert.throws(() => hp.read("../secret.md"), PrimError);

writeFileSync(join(house, "accounts.jsonl"), '{"id":"ACC-CHK","name":"Harbor Checking"}\n\n{"id":"ACC-HYSA"}\n', "utf8");
assert.deepEqual(
  hp.jsonl<{ id: string }>("accounts.jsonl").map((r) => r.id),
  ["ACC-CHK", "ACC-HYSA"],
);

const mem = openPrim({
  files: {
    "index.md": hp.read("index.md"),
    "log.md": hp.read("log.md"),
    "accounts.jsonl": hp.read("accounts.jsonl"),
  },
});
assert.equal(mem.title, "Harbor House");
assert.equal(mem.surface()?.name, "opff-editor");
assert.equal(mem.jsonl("accounts.jsonl").length, 2);
mem.close();
assert.throws(() =>
  createTool({
    name: "not-a-tool",
    kind: "script" as "surface",
    direction: "emit",
    cites: "obf:example",
  }),
);
assert.throws(() =>
  createTool({
    name: "orphan",
    kind: "surface",
    direction: "emit",
    cites: "",
  }),
);
assert.equal(viewKey({ profile: "obf", subtype: "picture-book", type: "Book" }), "obf/picture-book");
assert.equal(resolveView({ profile: "obf", subtype: "picture-book" }), FACE_VIEW);
assert.equal(p.view().key, "okf/face");
registerView(
  createView({
    key: "obf/picture-book",
    profile: "obf",
    subtype: "picture-book",
    projects: "scene+lines",
  }),
);
assert.equal(resolveView({ profile: "obf", subtype: "picture-book" }).projects, "scene+lines");
assert.equal(trustTier("human:daniel"), "human");
assert.equal(trustTier("agent:cursor"), "agent");
assert.equal(trustTier("0.9"), null);

registerValidator(
  createValidator({
    name: "obf-fixture",
    profile: "obf",
    run: (pack) => (pack.profile === "ocsf" ? ["fixture: not obf"] : []),
  }),
);
assert.deepEqual(validate(p), []);

const here = dirname(fileURLToPath(import.meta.url));
const morgan = join(here, "..", "..", "..", "..", "prim.obf", "examples", "metrics-gold-fairy-tale");
try {
  const m = openPrim(morgan);
  assert.equal(m.viewKey, "obf/picture-book");
  assert.equal(m.view().projects, "scene+lines");
  assert.ok(m.authorityPaths().includes("book.json"));
  assert.ok(m.constraintPaths().some((x) => x.includes("bible")));
  assert.ok(m.logFile());
  assert.deepEqual(m.validateBase(), []);
  assert.equal(m.trust(), "agent");
} catch (err) {
  if (err instanceof PrimError && err.message.includes("no index.md")) {
    /* sibling example not checked out */
  } else {
    throw err;
  }
}

const empty = join(tmp, "empty");
mkdirSync(empty);
assert.throws(() => openPrim(empty), PrimError);

process.stdout.write(
  "ok — face parse, primitives, prim tools, ui key, validator registry, zip+tar, base gates\n",
);
