/** Bounded data-only schema vocabulary for offline creation kits. No remote refs or code. */
export type JSONValue = null | boolean | number | string | JSONValue[] | { [key: string]: JSONValue };
export type JSONObject = { [key: string]: JSONValue };
export type ProfileProblem = { path: string; rule: string };
export class ProfileError extends Error {}
export function object(value: JSONValue): value is JSONObject { return value !== null && typeof value === "object" && !Array.isArray(value); }

export function bounded(value: JSONValue, depth = 0): void {
  if (depth > 24) throw new ProfileError("JSON nesting limit exceeded");
  if (typeof value === "number" && (!Number.isFinite(value) || Math.abs(value) > Number.MAX_SAFE_INTEGER)) throw new ProfileError("Number exceeds host numeric range");
  if (value && typeof value === "object") {
    const entries = Object.values(value);
    if (entries.length > 2048) throw new ProfileError("JSON container limit exceeded");
    for (const item of entries) bounded(item, depth + 1);
  }
}

export function parseProfileJSON(data: string | Uint8Array, maximum = 512 * 1024): JSONValue {
  if (Buffer.byteLength(data) > maximum) throw new ProfileError("JSON size limit exceeded");
  const raw = typeof data === "string" ? data : new TextDecoder("utf-8", { fatal: true }).decode(data);
  const stack: { keys: Set<string> | null; key: boolean }[] = [];
  for (let i = 0; i < raw.length; i++) {
    const char = raw[i];
    if (char === "{" || char === "[") {
      stack.push({ keys: char === "{" ? new Set() : null, key: char === "{" });
      if (stack.length > 24) throw new ProfileError("JSON nesting limit exceeded");
    } else if (char === "}" || char === "]") {
      if (!stack.pop()) throw new ProfileError("Invalid JSON");
    } else if (char === ",") {
      if (stack.at(-1)?.keys) stack.at(-1)!.key = true;
    } else if (char === '"') {
      const start = i++;
      while (i < raw.length) {
        if (raw[i] === "\\") { i += 2; continue; }
        if (raw[i] === '"') break;
        i++;
      }
      if (i >= raw.length) throw new ProfileError("Invalid JSON string");
      const frame = stack.at(-1);
      if (frame?.key) {
        const key = JSON.parse(raw.slice(start, i + 1));
        if (frame.keys!.has(key)) throw new ProfileError("Duplicate JSON field");
        frame.keys!.add(key); frame.key = false;
      }
    }
  }
  const result: JSONValue = JSON.parse(raw); bounded(result); return result;
}

const vocabulary = new Set(["$schema", "$id", "title", "description", "default", "examples", "type", "const", "enum", "properties", "required", "additionalProperties", "items", "minItems", "maxItems", "minLength", "maxLength", "minimum", "maximum", "allOf", "anyOf", "oneOf", "not", "if", "then", "else"]);
export function checkProfileSchema(schema: JSONValue): void {
  if (typeof schema === "boolean") return;
  if (!object(schema) || Object.keys(schema).some(key => !vocabulary.has(key))) throw new ProfileError("Unsupported schema assertion");
  if (Object.hasOwn(schema, "type")) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.length || types.some(t => typeof t !== "string" || !["object", "array", "string", "number", "integer", "boolean", "null"].includes(t))) throw new ProfileError("Invalid schema type");
  }
  if (Object.hasOwn(schema, "properties")) {
    if (!object(schema.properties)) throw new ProfileError("Invalid schema properties");
    for (const s of Object.values(schema.properties)) checkProfileSchema(s);
  }
  for (const key of ["items", "additionalProperties", "not", "if", "then", "else"]) if (Object.hasOwn(schema, key)) checkProfileSchema(schema[key]);
  for (const key of ["allOf", "anyOf", "oneOf"]) if (Object.hasOwn(schema, key)) {
    if (!Array.isArray(schema[key]) || !schema[key].length) throw new ProfileError("Invalid schema alternatives");
    for (const s of schema[key]) checkProfileSchema(s);
  }
  for (const key of ["minItems", "maxItems", "minLength", "maxLength", "minimum", "maximum"]) if (Object.hasOwn(schema, key) && typeof schema[key] !== "number") throw new ProfileError("Invalid schema limit");
  if (Object.hasOwn(schema, "required") && (!Array.isArray(schema.required) || schema.required.some(s => typeof s !== "string"))) throw new ProfileError("Invalid required fields");
  if (Object.hasOwn(schema, "enum") && (!Array.isArray(schema.enum) || !schema.enum.length)) throw new ProfileError("Invalid choices");
}

export function jsonEqual(a: JSONValue, b: JSONValue): boolean {
  if (a === b) return true;
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => jsonEqual(v, b[i]));
  if (object(a) && object(b)) return Object.keys(a).length === Object.keys(b).length && Object.keys(a).every(k => Object.hasOwn(b, k) && jsonEqual(a[k], b[k]));
  return false;
}

export function validateProfileSchema(record: JSONValue, schema: JSONValue): ProfileProblem[] {
  let budget = 50000;
  function walk(value: JSONValue, s: JSONValue, path: string): ProfileProblem[] {
    if (--budget < 0) return [{ path, rule: "validation_budget" }];
    if (s === true) return [];
    if (!object(s)) return [{ path, rule: "false_schema" }];
    const errors: ProfileProblem[] = [];
    const fail = (rule: string) => errors.push({ path, rule });
    if (Object.hasOwn(s, "type")) {
      const types = Array.isArray(s.type) ? s.type : [s.type];
      const kind = value === null ? "null" : Array.isArray(value) ? "array" : typeof value;
      if (!types.includes(kind) && !(types.includes("integer") && typeof value === "number" && Number.isInteger(value))) return [{ path, rule: "type" }];
    }
    if (Object.hasOwn(s, "const") && !jsonEqual(value, s.const)) fail("const");
    if (Array.isArray(s.enum) && !s.enum.some(v => jsonEqual(v, value))) fail("enum");
    if (typeof value === "string") {
      const length = [...value].length;
      if (typeof s.minLength === "number" && length < s.minLength) fail("minLength");
      if (typeof s.maxLength === "number" && length > s.maxLength) fail("maxLength");
    }
    if (typeof value === "number") {
      if (typeof s.minimum === "number" && value < s.minimum) fail("minimum");
      if (typeof s.maximum === "number" && value > s.maximum) fail("maximum");
    }
    if (Array.isArray(value)) {
      if (typeof s.minItems === "number" && value.length < s.minItems) fail("minItems");
      if (typeof s.maxItems === "number" && value.length > s.maxItems) fail("maxItems");
      if (Object.hasOwn(s, "items")) for (let i = 0; i < value.length && errors.length < 100 && budget >= 0; i++) errors.push(...walk(value[i], s.items, `${path}/${i}`));
    }
    if (object(value)) {
      const props = object(s.properties ?? null) ? s.properties as JSONObject : {};
      for (const key of (s.required as string[] ?? [])) if (!Object.hasOwn(value, key)) errors.push({ path: `${path}/${key}`, rule: "required" });
      for (const [key, v] of Object.entries(value)) {
        if (errors.length >= 100 || budget < 0) break;
        const escaped = key.replaceAll("~", "~0").replaceAll("/", "~1");
        if (Object.hasOwn(props, key)) errors.push(...walk(v, props[key], `${path}/${escaped}`));
        else if (Object.hasOwn(s, "additionalProperties")) errors.push(...walk(v, s.additionalProperties, `${path}/${escaped}`));
      }
    }
    for (const child of s.allOf as JSONValue[] ?? []) {
      errors.push(...walk(value, child, path)); if (errors.length >= 100 || budget < 0) break;
    }
    for (const key of ["anyOf", "oneOf"]) if (Array.isArray(s[key])) {
      let passed = 0;
      for (const child of s[key]) { if (!walk(value, child, path).length) passed++; if (budget < 0) break; }
      if (key === "anyOf" ? passed === 0 : passed !== 1) fail(key);
    }
    if (Object.hasOwn(s, "not") && !walk(value, s.not, path).length) fail("not");
    if (Object.hasOwn(s, "if")) {
      const branch = walk(value, s.if, path).length ? "else" : "then";
      if (Object.hasOwn(s, branch)) errors.push(...walk(value, s[branch], path));
    }
    if (budget < 0) fail("validation_budget");
    return errors.slice(0, 100);
  }
  return walk(record, schema, "");
}
