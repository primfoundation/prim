/** Filesystem adapter for complete packs. Private outputs, new destinations, no execution. */
import { existsSync, linkSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { decodeCompletePack, encodeCompletePack, MAX_TRANSFER_ARCHIVE, MAX_TRANSFER_FILE, MAX_TRANSFER_FILES, MAX_TRANSFER_TOTAL, requireTransferNames } from './complete-pack.ts';
import type { CompleteFiles, TransferSummary } from './complete-pack.ts';
import { ProfileError } from './profile-schema.ts';

function trusted(path: string): string {
  const full = resolve(path), parent = dirname(full);
  if (!lstatSync(parent).isDirectory() || realpathSync(parent) !== parent) throw new ProfileError('Choose a trusted local parent without symlinks');
  try { if (lstatSync(full).isSymbolicLink()) throw new ProfileError('Symlink paths are not supported'); }
  catch (e) { if ((e as NodeJS.ErrnoException).code !== 'ENOENT') throw e; }
  return full;
}
function readBounded(path: string, maximum: number): Uint8Array {
  const before = lstatSync(path, { bigint: true });
  if (!before.isFile() || before.isSymbolicLink() || before.size > BigInt(maximum)) throw new ProfileError('Select a bounded regular file');
  const raw = readFileSync(path), after = lstatSync(path, { bigint: true });
  if (raw.length > maximum || before.ino !== after.ino || before.size !== after.size || before.mtimeNs !== after.mtimeNs || before.ctimeNs !== after.ctimeNs) throw new ProfileError('Pack source changed during read');
  return raw;
}
export function readCompleteFolder(path: string): CompleteFiles {
  const root = trusted(path);
  if (!lstatSync(root).isDirectory() || realpathSync(root) !== root) throw new ProfileError('Choose a local directory without symlinks');
  const files: CompleteFiles = new Map(); let total = 0, directories = 0;
  function walk(dir: string): void {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name), name = relative(root, path).split(sep).join('/');
      requireTransferNames([name]);
      if (entry.isSymbolicLink()) throw new ProfileError('Symlinks are not transported');
      if (entry.isDirectory()) {
        if (++directories > MAX_TRANSFER_FILES) throw new ProfileError('Pack directory count limit exceeded');
        walk(path);
      } else {
        if (!entry.isFile() || files.size >= MAX_TRANSFER_FILES) throw new ProfileError('Pack file type or count limit exceeded');
        const raw = readBounded(path, Math.min(MAX_TRANSFER_FILE, MAX_TRANSFER_TOTAL - total));
        total += raw.length; files.set(name, raw);
      }
    }
  }
  walk(root); return files;
}
export async function exportCompletePack(source: string, output: string): Promise<TransferSummary> {
  const root = trusted(source), target = trusted(output);
  if (target === root || target.startsWith(root + sep)) throw new ProfileError('Export destination must be outside the source pack');
  const bytes = await encodeCompletePack(readCompleteFolder(root));
  const { summary } = await decodeCompletePack(bytes);
  const temp = mkdtempSync(join(dirname(target), '.prim-export-'));
  try {
    const file = join(temp, 'pack.zip');
    writeFileSync(file, bytes, { flag: 'wx', mode: 0o600, flush: true });
    linkSync(file, target);
  } finally { rmSync(temp, { recursive: true, force: true }); }
  return summary;
}
export async function importCompletePack(source: string, output: string, expectedSHA256?: string): Promise<TransferSummary> {
  const target = trusted(output);
  const { files, summary } = await decodeCompletePack(readBounded(trusted(source), MAX_TRANSFER_ARCHIVE), expectedSHA256);
  if (existsSync(target)) throw new ProfileError('Import requires a new directory');
  const temp = mkdtempSync(join(dirname(target), '.prim-transfer-'));
  try {
    for (const [name, bytes] of files) {
      const path = join(temp, name);
      mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
      writeFileSync(path, bytes, { flag: 'wx', mode: 0o600, flush: true });
    }
    if (existsSync(target)) throw new ProfileError('Import destination appeared during creation');
    renameSync(temp, target);
  } finally { rmSync(temp, { recursive: true, force: true }); }
  return summary;
}
export async function checkCompletePack(source: string, expectedSHA256?: string): Promise<TransferSummary> {
  return (await decodeCompletePack(readBounded(trusted(source), MAX_TRANSFER_ARCHIVE), expectedSHA256)).summary;
}
