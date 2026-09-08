import { execFileSync } from 'node:child_process';
import { copyFileSync, chmodSync, mkdirSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
rmSync(new URL('../dist', import.meta.url), {recursive:true, force:true});
execFileSync(process.execPath, [fileURLToPath(new URL('../node_modules/typescript/bin/tsc', import.meta.url)), '-p', 'tsconfig.build.json'], {cwd:root, stdio:'inherit'});
mkdirSync(new URL('../dist/data', import.meta.url), {recursive:true});
copyFileSync(new URL('../../../registry/registry.json', import.meta.url), new URL('../dist/data/registry.json', import.meta.url));
chmodSync(new URL('../dist/cli.js', import.meta.url), 0o755);
