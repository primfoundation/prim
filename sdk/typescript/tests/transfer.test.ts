import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ProfileLibrary } from '../src/profile-library.ts';
import { encodeCompletePack, decodeCompletePack, requireTransferNames, transferSHA256, MAX_TRANSFER_FILE, MAX_TRANSFER_FILES } from '../src/complete-pack.ts';
import { readCompleteFolder, exportCompletePack, importCompletePack } from '../src/pack-transfer.ts';

const encoder = new TextEncoder();
const base = () => new Map([
  ['index.md', encoder.encode('# Unknown profile\n')],
  ['prim-definition.lock.json', encoder.encode(JSON.stringify({profile_id:'outside/test',version:'1.0.0',definition_sha256:'a'.repeat(64)}))],
  ['evidence/original.bin', new Uint8Array([0,255,13,10,42])],
]);
test('byte-preserving deterministic envelope and trusted pin check', async () => {
  const input = base(), raw = await encodeCompletePack(input);
  const parsed = await decodeCompletePack(raw, await transferSHA256(raw));
  assert.deepEqual(parsed.files,input);
  assert.equal(parsed.summary.source_authentication,'not_verified');
  assert.deepEqual(await encodeCompletePack(new Map([...input].reverse())),raw);
  await assert.rejects(decodeCompletePack(raw,'0'.repeat(64)),/digest mismatch/);
});
test('copy input before async digest work', async () => {
  const files=base(), original=new Uint8Array(files.get('evidence/original.bin')!);
  const pending=encodeCompletePack(files);files.get('evidence/original.bin')![0]=99;files.clear();
  assert.deepEqual((await decodeCompletePack(await pending)).files.get('evidence/original.bin'),original);
});
test('unsafe portable paths and collisions fail', () => {
  for(const names of [['../x'],['/x'],['a\\b'],['a:b'],['a//b'],['a/./b'],['a.'],['CON.txt'],['a','A'],['a','a/b'],['a','A/b'],['a'.repeat(241)]]) assert.throws(()=>requireTransferNames(names));
});
test('reserved manifest, huge entries and too many files fail', async () => {
  const files=base();files.set('PRIM-TRANSFER.JSON',new Uint8Array());await assert.rejects(encodeCompletePack(files));
  files.delete('PRIM-TRANSFER.JSON');files.set('large.bin',new Uint8Array(MAX_TRANSFER_FILE+1));await assert.rejects(encodeCompletePack(files));
  files.delete('large.bin');for(let i=0;i<MAX_TRANSFER_FILES;i++)files.set('extra-'+i,new Uint8Array());await assert.rejects(encodeCompletePack(files));
});
test('ZIP corruption, unsupported forms and trailing bytes fail', async () => {
  const bytes=await encodeCompletePack(base()), original=new DataView(bytes.buffer), central=original.getUint32(bytes.length-6,true);
  for(const [offset,value,size] of [[central+8,0x801,2],[central+10,8,2],[central+38,0o120777<<16,4],[central+42,1,4],[central+24,MAX_TRANSFER_FILE+1,4],[central+30,1,2],[central+32,1,2]]) {
    const raw=new Uint8Array(bytes),view=new DataView(raw.buffer);if(size===2)view.setUint16(offset,value,true);else view.setUint32(offset,value,true);
    await assert.rejects(decodeCompletePack(raw));
  }
  await assert.rejects(decodeCompletePack(bytes.slice(0,-1)));
  const extra=new Uint8Array(bytes.length+1);extra.set(bytes);await assert.rejects(decodeCompletePack(extra));
});
test('Research cannot silently lose embedded evidence', async () => {
  const files=base();
  files.set('prim-definition.lock.json',encoder.encode(JSON.stringify({profile_id:'primfoundation/research',version:'0.3.0-dev.3',definition_sha256:'a'.repeat(64)})));
  const original=files.get('evidence/original.bin')!;
  files.set('research.json',encoder.encode(JSON.stringify({sources:[{artifact:{path:'evidence/original.bin',bytes:original.length,sha256:await transferSHA256(original)}}]})));
  await decodeCompletePack(await encodeCompletePack(files));
  files.delete('evidence/original.bin');await assert.rejects(encodeCompletePack(files),/Missing or changed embedded artifact/);
});
test('duplicate definition fields and missing lock fail', async () => {
  const files=base();files.set('prim-definition.lock.json',encoder.encode('{"profile_id":"outside/test","profile_id":"outside/test","version":"1.0.0","definition_sha256":"'+'a'.repeat(64)+'"}'));
  await assert.rejects(encodeCompletePack(files),/Duplicate/);
  files.delete('prim-definition.lock.json');await assert.rejects(encodeCompletePack(files));
});
test('all known profiles export to new files and import after source removal', async () => {
  const root=realpathSync(mkdtempSync(join(tmpdir(),'prim-complete-'))),library=new ProfileLibrary();
  try {
    for(const kit of library.list()) {
      const source=join(root,kit.name.replaceAll(' ','-')),zip=source+'.zip',target=source+'-restored';
      library.writePack(library.pin(kit),library.create(library.pin(kit)),source);
      writeFileSync(join(source,'unknown.bin'),new Uint8Array([0,255,1]));
      const expected=readCompleteFolder(source),summary=await exportCompletePack(source,zip);
      rmSync(source,{recursive:true});await importCompletePack(zip,target,summary.archive_sha256);
      assert.deepEqual(readCompleteFolder(target),expected);
      await assert.rejects(importCompletePack(zip,target));
      const before=readFileSync(zip);await assert.rejects(exportCompletePack(target,zip));assert.deepEqual(readFileSync(zip),before);
    }
  } finally {rmSync(root,{recursive:true,force:true});}
});
