/** Pinned offline profile packages, additive to the existing category registry. */
import { createHash, randomUUID } from "node:crypto";
import { lstatSync, readFileSync, realpathSync, mkdirSync, mkdtempSync, writeFileSync, renameSync, rmSync, existsSync } from "node:fs";
import { dirname, basename, join, resolve } from "node:path";
import { HOST_CATALOG_BASE64, HOST_CATALOG_SHA256 } from "./profile-data.ts";
import { ProfileError, bounded, checkProfileSchema, object, parseProfileJSON, validateProfileSchema } from "./profile-schema.ts";
import type { JSONValue, JSONObject, ProfileProblem } from "./profile-schema.ts";

export { ProfileError, parseProfileJSON } from "./profile-schema.ts";
export type { JSONValue, ProfileProblem } from "./profile-schema.ts";
export type DefinitionPin = { profile_id: string; version: string; definition_sha256: string };
export type CreationKit = DefinitionPin & { name: string; authority_file: string; identity_field: string; title_field: string; schema: JSONValue; template: JSONObject; rules: JSONObject };

export class ProfileLibrary {
  readonly catalogSHA256: string;
  readonly sourceCommit: string;
  private readonly entries = new Map<string, CreationKit>();

  constructor(data: Uint8Array = Buffer.from(HOST_CATALOG_BASE64, "base64"), expectedSHA256 = HOST_CATALOG_SHA256) {
    this.catalogSHA256 = createHash("sha256").update(data).digest("hex");
    if (this.catalogSHA256 !== expectedSHA256) throw new ProfileError("Catalog checksum mismatch");
    const catalog = parseProfileJSON(data, 8 * 1024 * 1024);
    if (!object(catalog) || catalog.format !== "prim-host-catalog" || catalog.version !== 1 || !Array.isArray(catalog.kits) || !catalog.kits.length) throw new ProfileError("Unsupported host catalog");
    this.sourceCommit = String(catalog.source_commit ?? "unrecorded");
    for (const raw of catalog.kits) {
      if (!object(raw) || typeof raw.profile_id !== "string" || !/^[a-z][a-z0-9-]{0,63}\/[a-z][a-z0-9-]{0,63}$/.test(raw.profile_id)
          || typeof raw.version !== "string" || typeof raw.definition_sha256 !== "string" || !/^[0-9a-f]{64}$/.test(raw.definition_sha256)
          || typeof raw.authority_file !== "string" || !/^[a-z][a-z0-9-]*\.json$/.test(raw.authority_file)
          || typeof raw.identity_field !== "string" || typeof raw.title_field !== "string" || !object(raw.template) || !object(raw.rules)) throw new ProfileError("Invalid creation kit");
      checkProfileSchema(raw.schema);
      const strings = ["unique_ids", "token_fields"];
      const fields: Record<string, string[]> = { root_references: ["field", "target"], references: ["collection", "field", "target"], required_links: ["collection", "when_field", "when_value", "links", "reference_field", "relation"] };
      for (const [key, entries] of Object.entries(raw.rules)) {
        if ((!strings.includes(key) && !Object.hasOwn(fields, key)) || !Array.isArray(entries)) throw new ProfileError("Unsupported reference rules");
        for (const entry of entries) {
          if (strings.includes(key) ? typeof entry !== "string" : !object(entry) || Object.keys(entry).length !== fields[key].length || fields[key].some(k => typeof entry[k] !== "string")) throw new ProfileError("Invalid reference rule");
        }
      }
      const kit = structuredClone(raw) as unknown as CreationKit;
      const key = `${kit.profile_id}@${kit.version}`;
      if (this.entries.has(key)) throw new ProfileError("Duplicate profile version");
      this.entries.set(key, kit);
      this.create(this.pin(kit));
    }
  }

  list(): CreationKit[] { return structuredClone([...this.entries.values()]); }
  pin(kit: DefinitionPin): DefinitionPin { return { profile_id: kit.profile_id, version: kit.version, definition_sha256: kit.definition_sha256 }; }
  get(pin: DefinitionPin): CreationKit {
    const kit = this.entries.get(`${pin.profile_id}@${pin.version}`);
    if (!kit || kit.definition_sha256 !== pin.definition_sha256) throw new ProfileError("Exact pinned definition unavailable; no upgrade applied");
    return structuredClone(kit);
  }

  create(pin: DefinitionPin, values: JSONObject = {}): JSONObject {
    const kit = this.get(pin);
    const record = { ...kit.template, ...structuredClone(values) };
    if (!record[kit.identity_field]) record[kit.identity_field] = `prim-${randomUUID().replaceAll("-", "")}`;
    this.requireValid(pin, record);
    return record;
  }

  validate(pin: DefinitionPin, record: JSONValue): ProfileProblem[] {
    bounded(record);
    if (Buffer.byteLength(JSON.stringify(record)) > 512 * 1024) throw new ProfileError("Record size limit exceeded");
    const kit = this.get(pin), errors = validateProfileSchema(record, kit.schema);
    if (errors.length || !object(record)) return errors;
    const rules = kit.rules;
    const rows = (field: JSONValue): JSONObject[] => typeof field === "string" && Object.hasOwn(record, field) && Array.isArray(record[field]) ? record[field] as JSONObject[] : [];
    const ids = (field: JSONValue) => new Set(rows(field).map(row => row.id));
    const fail = (path: string, rule: string) => errors.push({ path, rule });
    for (const field of rules.unique_ids as string[] ?? []) if (ids(field).size !== rows(field).length) fail(field, "duplicate_id");
    for (const field of rules.token_fields as string[] ?? []) if (typeof record[field] !== "string" || !/^[a-z][a-z0-9.-]*$/.test(record[field])) fail(field, "invalid_token");
    for (const rule of rules.root_references as JSONObject[] ?? []) {
      const field = rule.field as string, ref = record[field];
      if (ref !== null && ref !== undefined && !ids(rule.target).has(ref)) fail(field, "unresolved_reference");
    }
    for (const rule of rules.references as JSONObject[] ?? []) {
      const field = rule.field as string, targets = ids(rule.target);
      rows(rule.collection).forEach((row, i) => { if (row[field] !== null && row[field] !== undefined && !targets.has(row[field])) fail(`${rule.collection}/${i}/${field}`, "unresolved_reference"); });
    }
    for (const rule of rules.required_links as JSONObject[] ?? []) {
      rows(rule.collection).forEach((row, i) => {
        if (row[rule.when_field as string] === rule.when_value && !rows(rule.links).some(link => link[rule.reference_field as string] === row.id && link.relation === rule.relation)) fail(`${rule.collection}/${i}`, "missing_declared_support");
      });
    }
    return errors.slice(0, 100);
  }

  requireValid(pin: DefinitionPin, record: JSONValue): void {
    const errors = this.validate(pin, record);
    if (errors.length) throw new ProfileError(errors.slice(0, 8).map(e => `${e.path}: ${e.rule}`).join("\n"));
  }

  readPack(path: string): { pin: DefinitionPin; record: JSONObject } {
    const root = resolve(path);
    if (!lstatSync(root).isDirectory() || realpathSync(root) !== root) throw new ProfileError("Choose a local directory without symlinks");
    const read = (name: string): JSONValue => {
      const file = join(root, name), stat = lstatSync(file);
      if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 512 * 1024) throw new ProfileError("Invalid or oversized Prim file");
      return parseProfileJSON(readFileSync(file));
    };
    const rawPin = read("prim-definition.lock.json");
    if (!object(rawPin)) throw new ProfileError("Invalid definition lock");
    const pin = rawPin as unknown as DefinitionPin, kit = this.get(pin);
    const record = read(kit.authority_file);
    this.requireValid(pin, record);
    return { pin: this.pin(pin), record: record as JSONObject };
  }

  writePack(pin: DefinitionPin, record: JSONObject, path: string): void {
    const kit = this.get(pin); this.requireValid(pin, record);
    // Validate the actual exported representation before creating any directory.
    // Pretty printing can exceed the reader's byte budget even when compact JSON fits.
    const recordText = JSON.stringify(record, null, 2) + "\n";
    parseProfileJSON(recordText);
    const target = resolve(path), parent = dirname(target);
    if (!lstatSync(parent).isDirectory() || realpathSync(parent) !== parent) throw new ProfileError("Choose a trusted local parent without symlinks");
    try { lstatSync(target); throw new ProfileError("Export requires a new directory"); } catch (e) { if ((e as NodeJS.ErrnoException).code !== "ENOENT") throw e; }
    const temp = mkdtempSync(join(parent, ".prim-create-"));
    try {
      const write = (name: string, text: string) => writeFileSync(join(temp, name), text, { flag: "wx", mode: 0o600, flush: true });
      write(kit.authority_file, recordText);
      write("prim-definition.lock.json", JSON.stringify(this.pin(pin), null, 2) + "\n");
      write("index.md", `---\nprofile: ${JSON.stringify(pin.profile_id)}\nprofile_version: ${JSON.stringify(pin.version)}\ntype: ${JSON.stringify(pin.profile_id.split("/").at(-1))}\ntitle: ${JSON.stringify(record[kit.title_field] ?? kit.name)}\nauthority: ${kit.authority_file}\n---\n\nThe authoritative record is in \`${kit.authority_file}\`.\n`);
      write("log.md", "# Log\n\n- Created locally using a pinned definition. Structural validation does not verify facts or authority.\n");
      if (existsSync(target)) throw new ProfileError("Target appeared during creation");
      renameSync(temp, target);
    } finally { rmSync(temp, { recursive: true, force: true }); }
  }
}
