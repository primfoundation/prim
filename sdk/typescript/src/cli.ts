#!/usr/bin/env node
/** Category CLI. Profile validators register on the SDK; this is not a book tool. */

import { PrimError, openPrim } from "./pack.ts";
import { getApplet, getTool, getType, listApplets, listTools, listTypes } from "./registry.ts";
import { ProfileLibrary, ProfileError, parseProfileJSON } from "./profile-library.ts";
import { object } from "./profile-schema.ts";
import { lstatSync, readFileSync } from "node:fs";

const args = process.argv.slice(2);
const cmd = args[0];

if (!cmd) {
  usage();
  process.exit(2);
}

try {
  if (cmd === "profile") {
    profileCmd(args.slice(1));
    process.exit(0);
  }
  if (cmd === "registry") {
    registryCmd(args.slice(1));
    process.exit(0);
  }
  const target = args[1];
  if (!target) {
    usage();
    process.exit(2);
  }
  const pack = openPrim(target);
  if (cmd === "open") {
    const pair = pack.pair();
    process.stdout.write(
      `${JSON.stringify({
        profile: pair.profile,
        type: pack.type,
        subtype: pack.subtype,
        title: pair.title,
        viewKey: pair.viewKey,
        trust: pack.trust(),
        tools: pair.tools.map((t) => t.name),
        surface: pair.surface?.name ?? null,
        connector: pair.connector?.name ?? null,
      })}\n`,
    );
    pack.close();
    process.exit(0);
  }
  if (cmd === "tools") {
    process.stdout.write(`${JSON.stringify(pack.pair(), null, 2)}\n`);
    pack.close();
    process.exit(0);
  }
  if (cmd === "validate") {
    const problems = pack.validate();
    for (const item of problems) process.stdout.write(`${item}\n`);
    pack.close();
    process.exit(problems.length ? 1 : 0);
  }
  usage();
  process.exit(2);
} catch (err) {
  if (err instanceof PrimError || err instanceof ProfileError) {
    console.error(err.message);
    process.exit(1);
  }
  throw err;
}

function usage(): void {
  console.error("usage: prim <open|validate|tools> <path>");
  console.error("       prim registry [types|tools [citing <type>]|applets|type <name>|tool <name>|applet <id>]");
  console.error("       prim profile list");
  console.error("       prim profile create <namespace/name> --version <exact-version> --output <new-folder> [--input <record.json>]");
  console.error("       prim profile check <folder>");
}

function profileCmd(rest: string[]): void {
  const library = new ProfileLibrary();
  if (rest.length === 1 && rest[0] === "list") {
    for (const kit of library.list()) process.stdout.write(JSON.stringify({ ...library.pin(kit), name: kit.name }) + "\n");
    return;
  }
  if (rest.length === 2 && rest[0] === "check") {
    const { pin } = library.readPack(rest[1]);
    process.stdout.write(JSON.stringify({ status: "passed", pin, checks: { structure_and_declared_references: "passed", factual_accuracy: "not_checked", authorization: "not_verified" } }) + "\n");
    return;
  }
  if (rest[0] === "create" && rest.length >= 6) {
    const flags = new Map<string, string>();
    for (let i = 2; i < rest.length; i += 2) {
      if (!["--version", "--output", "--input"].includes(rest[i]) || flags.has(rest[i]) || rest[i + 1] === undefined) throw new ProfileError("Unknown, repeated or incomplete creation option");
      flags.set(rest[i], rest[i + 1]);
    }
    const kit = library.list().find(k => k.profile_id === rest[1] && k.version === flags.get("--version"));
    if (!kit || !flags.get("--output")) throw new ProfileError("An available exact version and new output folder are required");
    let input = {};
    if (flags.has("--input")) {
      const path = flags.get("--input")!, stat = lstatSync(path);
      if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 512 * 1024) throw new ProfileError("Input must be a bounded local JSON file");
      const value = parseProfileJSON(readFileSync(path));
      if (!object(value)) throw new ProfileError("Input must be a record object");
      input = value;
    }
    const pin = library.pin(kit), record = library.create(pin, input);
    library.writePack(pin, record, flags.get("--output")!);
    process.stdout.write(JSON.stringify({ status: "created", pin }) + "\n");
    return;
  }
  throw new ProfileError("Use prim profile list, create or check; creation requires an exact version");
}

function registryCmd(rest: string[]): void {
  const sub = rest[0] ?? "all";
  if (sub === "types" || sub === "all") {
    if (sub === "all") process.stdout.write("types:\n");
    for (const t of listTypes()) {
      process.stdout.write(`${t.name}\t${t.repo}\t${t.okf ? "okf" : "store"}\t${t.status}\n`);
    }
  }
  if (sub === "tools" || sub === "all") {
    if (sub === "all") process.stdout.write("tools:\n");
    const cites = rest[1] === "citing" ? rest[2] : undefined;
    for (const tool of listTools(cites ? { cites } : undefined)) {
      process.stdout.write(
        `${tool.name}\t${tool.kind}/${tool.direction}\tcites ${tool.cites}${tool.as ? `\tas ${tool.as}` : ""}\n`,
      );
    }
  }
  if (sub === "applets" || sub === "all") {
    if (sub === "all") process.stdout.write("applets:\n");
    for (const applet of listApplets()) {
      const prims = applet.prims.length ? applet.prims.join(",") : "-";
      process.stdout.write(`${applet.id}\t${applet.name}\t${applet.repo}\t${applet.status}\tprims ${prims}\n`);
    }
  }
  if (sub === "types" || sub === "tools" || sub === "applets" || sub === "all") return;
  if (sub === "type") {
    const name = rest[1];
    const t = name ? getType(name) : undefined;
    if (!t) {
      console.error(name ? `unknown type: ${name}` : "usage: prim registry type <name>");
      process.exit(1);
    }
    process.stdout.write(`${JSON.stringify(t, null, 2)}\n`);
    return;
  }
  if (sub === "tool") {
    const name = rest[1];
    const tool = name ? getTool(name) : undefined;
    if (!tool) {
      console.error(name ? `unknown tool: ${name}` : "usage: prim registry tool <name>");
      process.exit(1);
    }
    process.stdout.write(`${JSON.stringify(tool, null, 2)}\n`);
    return;
  }
  if (sub === "applet") {
    const id = rest[1];
    const applet = id ? getApplet(id) : undefined;
    if (!applet) {
      console.error(id ? `unknown applet: ${id}` : "usage: prim registry applet <id>");
      process.exit(1);
    }
    process.stdout.write(`${JSON.stringify(applet, null, 2)}\n`);
    return;
  }
  usage();
  process.exit(2);
}
