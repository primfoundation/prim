/** Portable complete-pack ZIP STORE envelope. Browser/Node; no network or code execution. */
import { object, parseProfileJSON, ProfileError } from './profile-schema.ts';
import type { JSONValue } from './profile-schema.ts';

export const TRANSFER_MANIFEST = 'prim-transfer.json';
export const MAX_TRANSFER_FILES = 256;
export const MAX_TRANSFER_FILE = 16 * 1024 * 1024;
export const MAX_TRANSFER_TOTAL = 32 * 1024 * 1024;
export const MAX_TRANSFER_ARCHIVE = 34 * 1024 * 1024;
const MAX_DOCUMENT = 512 * 1024, LOCK = 'prim-definition.lock.json';
const encoder = new TextEncoder(), decoder = new TextDecoder('utf-8', { fatal: true });
export type CompleteFiles = Map<string, Uint8Array>;
export type TransferPin = { profile_id: string; version: string; definition_sha256: string };
export type TransferSummary = { archive_sha256: string; manifest_sha256: string; files: number; total_bytes: number; pin: TransferPin; integrity: 'passed'; source_authentication: 'not_verified'; content_execution: 'not_performed' };
function fail(message = 'Invalid complete pack: compressed, encrypted, linked, ambiguous or corrupt entries are refused'): never { throw new ProfileError(message); }
export async function transferSHA256(bytes: Uint8Array): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new Uint8Array(bytes).buffer);
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}
function canonical(value: JSONValue): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (object(value)) return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
export function requireTransferNames(names: Iterable<string>): void {
  const folded = new Set<string>();
  for (const name of names) {
    if (name.length > 240 || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,119}(?:\/[A-Za-z0-9][A-Za-z0-9._-]{0,119}){0,7}$/.test(name)) fail('Unsupported portable pack path; names are never silently rewritten');
    if (name.split('/').some(p => p.endsWith('.') || /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(p))) fail('Nonportable pack path');
    const lower = name.toLowerCase();
    if (folded.has(lower)) fail('Duplicate or case-colliding pack path');
    folded.add(lower);
  }
  for (const name of folded) {
    const parts = name.split('/');
    for (let i = 1; i < parts.length; i++) if (folded.has(parts.slice(0, i).join('/'))) fail('File/directory path collision');
  }
}
async function definition(files: CompleteFiles): Promise<TransferPin> {
  if (!files.has(LOCK) || !files.has('index.md')) fail('Complete pack requires its definition lock and index.md');
  const pin = parseProfileJSON(files.get(LOCK)!);
  if (!object(pin) || Object.keys(pin).sort().join(',') !== 'definition_sha256,profile_id,version'
      || typeof pin.profile_id !== 'string' || !/^[a-z][a-z0-9-]{0,63}\/[a-z][a-z0-9-]{0,63}$/.test(pin.profile_id)
      || typeof pin.version !== 'string' || !/^[0-9A-Za-z.+-]{1,128}$/.test(pin.version)
      || typeof pin.definition_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(pin.definition_sha256)) fail('Invalid exact definition lock');
  if (pin.profile_id === 'primfoundation/research') {
    if (!files.has('research.json')) fail('Missing authoritative Research record');
    const record = parseProfileJSON(files.get('research.json')!);
    if (!object(record) || !Array.isArray(record.sources ?? [])) fail('Invalid Research sources');
    for (const source of record.sources as JSONValue[] ?? []) {
      if (!object(source) || !Object.hasOwn(source, 'artifact')) continue;
      const a = source.artifact;
      if (!object(a) || typeof a.path !== 'string') fail('Invalid embedded artifact reference');
      const bytes = files.get(a.path);
      if (!bytes || !Number.isSafeInteger(a.bytes) || bytes.length !== a.bytes || await transferSHA256(bytes) !== a.sha256) fail('Missing or changed embedded artifact; no incomplete export');
    }
  }
  return pin as TransferPin;
}
async function inventory(files: CompleteFiles): Promise<JSONValue> {
  if (files.size < 2 || files.size > MAX_TRANSFER_FILES || [...files.keys()].some(n => n.toLowerCase() === TRANSFER_MANIFEST)) fail('Pack file count or reserved transfer-manifest collision');
  requireTransferNames(files.keys());
  let total = 0;
  for (const raw of files.values()) {
    if (!(raw instanceof Uint8Array) || raw.length > MAX_TRANSFER_FILE) fail('Pack file byte limit exceeded');
    total += raw.length;
  }
  if (total > MAX_TRANSFER_TOTAL) fail('Complete pack total byte limit exceeded');
  const rows = [];
  for (const name of [...files.keys()].sort()) {
    const raw = files.get(name)!;
    rows.push({ bytes: raw.length, path: name, sha256: await transferSHA256(raw) });
  }
  return { definition: await definition(files), files: rows, format: 'prim-complete-pack', version: 1 };
}
const crcTable = Array.from({ length: 256 }, (_, i) => {
  let n = i; for (let j = 0; j < 8; j++) n = (n >>> 1) ^ ((n & 1) ? 0xedb88320 : 0);
  return n >>> 0;
});
function crc32(bytes: Uint8Array): number {
  let n = 0xffffffff; for (const byte of bytes) n = (n >>> 8) ^ crcTable[(n ^ byte) & 255];
  return (n ^ 0xffffffff) >>> 0;
}
export async function encodeCompletePack(input: CompleteFiles): Promise<Uint8Array> {
  // Take a bounded byte snapshot before awaits; caller edits cannot race hashing.
  if (input.size > MAX_TRANSFER_FILES) fail('Pack file count limit exceeded');
  let total = 0;
  for (const raw of input.values()) {
    if (!(raw instanceof Uint8Array) || raw.length > MAX_TRANSFER_FILE) fail('Pack file byte limit exceeded');
    total += raw.length; if (total > MAX_TRANSFER_TOTAL) fail('Pack total byte limit exceeded');
  }
  const files = new Map([...input].map(([n, b]) => [n, new Uint8Array(b)]));
  const manifest = encoder.encode(canonical(await inventory(files)) + '\n');
  if (manifest.length > MAX_DOCUMENT) fail('Transfer manifest byte limit exceeded');
  const entries = [[TRANSFER_MANIFEST, manifest] as const, ...[...files].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)]
    .map(([name, data]) => ({ name: encoder.encode(name), data }));
  const localSize = entries.reduce((s, f) => s + 30 + f.name.length + f.data.length, 0);
  const centralSize = entries.reduce((s, f) => s + 46 + f.name.length, 0);
  if (localSize + centralSize + 22 > MAX_TRANSFER_ARCHIVE) fail();
  const bytes = new Uint8Array(localSize + centralSize + 22), view = new DataView(bytes.buffer);
  let local = 0, central = localSize;
  for (const f of entries) {
    const crc = crc32(f.data);
    view.setUint32(local, 0x04034b50, true); view.setUint16(local + 4, 20, true); view.setUint16(local + 6, 0x800, true); view.setUint16(local + 12, 33, true);
    view.setUint32(local + 14, crc, true); view.setUint32(local + 18, f.data.length, true); view.setUint32(local + 22, f.data.length, true); view.setUint16(local + 26, f.name.length, true);
    bytes.set(f.name, local + 30); bytes.set(f.data, local + 30 + f.name.length);
    view.setUint32(central, 0x02014b50, true); view.setUint16(central + 4, 0x0314, true); view.setUint16(central + 6, 20, true); view.setUint16(central + 8, 0x800, true); view.setUint16(central + 14, 33, true);
    view.setUint32(central + 16, crc, true); view.setUint32(central + 20, f.data.length, true); view.setUint32(central + 24, f.data.length, true); view.setUint16(central + 28, f.name.length, true);
    view.setUint32(central + 38, (0o100600 << 16) >>> 0, true); view.setUint32(central + 42, local, true); bytes.set(f.name, central + 46);
    local += 30 + f.name.length + f.data.length; central += 46 + f.name.length;
  }
  view.setUint32(central, 0x06054b50, true); view.setUint16(central + 8, entries.length, true); view.setUint16(central + 10, entries.length, true);
  view.setUint32(central + 12, centralSize, true); view.setUint32(central + 16, localSize, true);
  return bytes;
}
export async function decodeCompletePack(input: Uint8Array, expectedSHA256?: string): Promise<{ files: CompleteFiles; summary: TransferSummary }> {
  if (!(input instanceof Uint8Array) || input.length < 22 || input.length > MAX_TRANSFER_ARCHIVE) fail();
  const bytes = new Uint8Array(input), view = new DataView(bytes.buffer), end = bytes.length - 22;
  const digest = await transferSHA256(bytes);
  if (expectedSHA256 !== undefined && (!/^[0-9a-f]{64}$/.test(expectedSHA256) || digest !== expectedSHA256)) fail('Complete archive digest mismatch');
  const u16 = (o: number) => view.getUint16(o, true), u32 = (o: number) => view.getUint32(o, true);
  const count = u16(end + 10), start = u32(end + 16), size = u32(end + 12);
  if (u32(end) !== 0x06054b50 || u16(end + 4) || u16(end + 6) || count !== u16(end + 8) || count < 3 || count > MAX_TRANSFER_FILES + 1 || u16(end + 20) || start + size !== end) fail();
  const files: CompleteFiles = new Map(); let local = 0, central = start, total = 0;
  for (let i = 0; i < count; i++) {
    if (central + 46 > end) fail();
    const length = u32(central + 24), nameSize = u16(central + 28), crc = u32(central + 16);
    if (u32(central) !== 0x02014b50 || u16(central + 4) !== 0x0314 || u16(central + 6) !== 20 || u16(central + 8) !== 0x800 || u16(central + 10)
        || u32(central + 20) !== length || length > MAX_TRANSFER_FILE || u16(central + 30) || u16(central + 32) || u16(central + 34) || u16(central + 36)
        || u32(central + 38) !== (0o100600 << 16) >>> 0 || u32(central + 42) !== local || central + 46 + nameSize > end || local + 30 + nameSize + length > start) fail();
    const name = decoder.decode(bytes.subarray(central + 46, central + 46 + nameSize));
    if (files.has(name) || u32(local) !== 0x04034b50 || u16(local + 4) !== 20 || u16(local + 6) !== 0x800 || u16(local + 8)
        || u16(local + 10) !== u16(central + 12) || u16(local + 12) !== u16(central + 14) || u32(local + 14) !== crc
        || u32(local + 18) !== length || u32(local + 22) !== length || u16(local + 26) !== nameSize || u16(local + 28)
        || decoder.decode(bytes.subarray(local + 30, local + 30 + nameSize)) !== name) fail();
    const data = bytes.slice(local + 30 + nameSize, local + 30 + nameSize + length);
    if (crc32(data) !== crc) fail();
    files.set(name, data); total += length; if (total > MAX_TRANSFER_TOTAL + MAX_DOCUMENT) fail();
    local += 30 + nameSize + length; central += 46 + nameSize;
  }
  if (local !== start || central !== end || !files.has(TRANSFER_MANIFEST)) fail();
  requireTransferNames(files.keys());
  const manifest = files.get(TRANSFER_MANIFEST)!; files.delete(TRANSFER_MANIFEST);
  const expected = await inventory(files);
  parseProfileJSON(manifest);
  if (decoder.decode(manifest) !== canonical(expected) + '\n') fail('Complete pack inventory or digest mismatch');
  return { files, summary: { archive_sha256: digest, manifest_sha256: await transferSHA256(manifest), files: files.size,
    total_bytes: [...files.values()].reduce((n, b) => n + b.length, 0), pin: (expected as { definition: TransferPin }).definition,
    integrity: 'passed', source_authentication: 'not_verified', content_execution: 'not_performed' } };
}
