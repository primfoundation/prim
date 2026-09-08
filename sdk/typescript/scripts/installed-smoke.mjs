import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, copyFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = resolve(process.argv[2] ?? join(root, 'artifacts'));
mkdirSync(output, {recursive:true});
const temp = mkdtempSync(join(tmpdir(), 'prim-installed-'));
try {
  execFileSync('npm', ['run', 'build'], {cwd:root, stdio:'inherit'});
  const packed = JSON.parse(execFileSync('npm', ['pack', '--ignore-scripts', '--json', '--pack-destination', output], {cwd:root, encoding:'utf8'}))[0];
  const archive = join(output, packed.filename);
  execFileSync('npm', ['install', '--ignore-scripts', '--offline', '--no-audit', '--no-fund', archive], {cwd:temp, stdio:'pipe'});
  const test = `import assert from 'node:assert/strict';
import {ProfileLibrary, listTypes, VERSION} from '@eidos-agi/prim';
assert.equal(VERSION,'0.5.0-dev.2'); assert.ok(listTypes().length > 0);
const library=new ProfileLibrary(); assert.equal(library.list().length,4);
for (const kit of library.list()) {
 const pin=library.pin(kit), record=library.create(pin,{extension:{retained:'outside checkout'}});
 const target=new URL('./'+kit.profile_id.split('/').at(-1),import.meta.url).pathname;
 library.writePack(pin,record,target);assert.deepEqual(library.readPack(target),{pin,record});
}
console.log(JSON.stringify({installed:true,profiles:library.list().length,registry:listTypes().length}));`;
  writeFileSync(join(temp,'smoke.mjs'), test);
  const result = JSON.parse(execFileSync(process.execPath, ['smoke.mjs'], {cwd:temp,encoding:'utf8'}));
  const cli = join(temp,'node_modules/.bin/prim');
  assert.equal(execFileSync(cli,['profile','list'],{cwd:temp,encoding:'utf8'}).trim().split('\n').length,4);
  assert.equal(JSON.parse(execFileSync(cli,['profile','check',join(temp,'person')],{cwd:temp,encoding:'utf8'})).status,'passed');
  writeFileSync(join(temp,'types.mts'), `import {ProfileLibrary, type DefinitionPin} from '@eidos-agi/prim';\nconst library = new ProfileLibrary();\nconst pin: DefinitionPin = library.pin(library.list()[0]);\nlibrary.validate(pin, library.create(pin));\n`);
  execFileSync(process.execPath,[join(root,'node_modules/typescript/bin/tsc'),'--noEmit','--module','NodeNext','--target','ES2022','--typeRoots',join(root,'node_modules/@types'),join(temp,'types.mts')],{cwd:temp,stdio:'inherit'});
  const report = {...result, cli:true, types:true, archive:packed.filename, sha256:createHash('sha256').update(readFileSync(archive)).digest('hex'), scope:'Clean offline tarball installation, compiled Node API and CLI, declarations and local pack round trips; no package-index publication'};
  writeFileSync(join(output,'installed-smoke.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
} finally { rmSync(temp,{recursive:true,force:true}); }
