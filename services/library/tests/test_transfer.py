"""Complete evidence transfer, hostile envelope rejection and independent SDK exchange."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zlib

from prim_library.cli import create
from prim_library.ingestion import capture_research, check_capture
from prim_library.library import Library, LibraryError, canonical
from prim_library.transfer import (decode_files, encode_files, export_pack, import_pack, read_folder,
                                   MANIFEST, MAX_FILE, MAX_TOTAL, MAX_FILES, names_valid)

ROOT = Path(__file__).resolve().parents[3]


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.library = Library()
        self.pack = self.root/'pack'; self.archive = self.root/'evidence.prim.zip'
        self.raw = b'Original\r\nevidence\x00\xff' * 100
        source = self.root/'source.bin'; source.write_bytes(self.raw)
        self.capture = self.root/'capture.json'
        self.capture.write_bytes(canonical({'format':'prim-artifact-capture','version':1,'operation_id':'transfer-test',
            'title':'Evidence transfer','question':None,'sources':[{'id':'source-1','path':'source.bin','locator':'urn:test:original',
            'sha256':hashlib.sha256(self.raw).hexdigest(),'media_type':'application/octet-stream','observed_at':None,
            'permissions':{'may_store':True,'may_share':False,'basis_as_recorded':'Synthetic local test'}}]}))
        self.receipt = capture_research(self.library, '0.3.0-dev.3', self.capture, self.pack)['receipt_sha256']

    def test_original_bytes_and_capture_receipt_survive_source_deletion(self):
        original = read_folder(self.pack)
        result = export_pack(self.pack,self.archive)
        shutil.rmtree(self.pack); (self.root/'source.bin').unlink(); self.capture.unlink()
        target=self.root/'restored'
        restored=import_pack(self.archive,target,result['archive_sha256'])
        self.assertEqual(original,read_folder(target))
        self.assertEqual(restored['source_authentication'],'not_verified')
        self.assertEqual(check_capture(self.library,target,self.receipt)['status'],'passed')
        self.assertFalse((target/MANIFEST).exists())
        if os.name=='posix':
            self.assertEqual(target.stat().st_mode&0o777,0o700)
            self.assertTrue(all(p.stat().st_mode&0o777==0o600 for p in target.rglob('*') if p.is_file()))

    def test_unknown_profile_and_binary_files_remain_opaque(self):
        files={'index.md':b'# Unknown\n','prim-definition.lock.json':canonical({'profile_id':'outside/new-kind','version':'1.0.0','definition_sha256':'a'*64}),
               'unknown.data':b'\xff\x00\r\n','nested/archive.zip':b'not-expanded','run.sh':b'never executed'}
        self.assertEqual(decode_files(encode_files(files))[0],files)

    def test_deterministic_archive(self):
        files=read_folder(self.pack)
        self.assertEqual(encode_files(files),encode_files(dict(reversed(list(files.items())))))

    def test_missing_or_modified_artifact_refuses_export(self):
        blob=next((self.pack/'artifacts').iterdir())
        blob.write_bytes(b'changed')
        with self.assertRaisesRegex(LibraryError,'missing or changed'):
            export_pack(self.pack,self.archive)
        self.assertFalse(self.archive.exists())
        blob.unlink()
        with self.assertRaises(LibraryError):export_pack(self.pack,self.archive)

    def test_all_four_known_profiles_transfer(self):
        for entry in self.library.search()['items']:
            identity=entry['id']
            folder=self.root/identity.split('/')[1]
            create(self.library,identity,entry['version'],folder)
            self.assertEqual(decode_files(encode_files(read_folder(folder)))[0],read_folder(folder))

    def test_symlink_and_special_source_fail_without_output(self):
        (self.pack/'link').symlink_to(self.root/'source.bin')
        with self.assertRaises(LibraryError):export_pack(self.pack,self.archive)
        self.assertFalse(self.archive.exists()); (self.pack/'link').unlink()
        if hasattr(os,'mkfifo'):
            os.mkfifo(self.pack/'fifo')
            with self.assertRaises(LibraryError):export_pack(self.pack,self.archive)

    def test_unsafe_case_reserved_and_prefix_paths_fail(self):
        for names in [['../x'],['/x'],['a\\b'],['a:b'],['a//b'],['a/./b'],['a.'],['CON.txt'],['a','A'],['a','a/b'],['a','A/b'],['a'*241],['a/'+('b/'*8)+'c']]:
            with self.subTest(names=names),self.assertRaises(LibraryError):names_valid(names)
        files=read_folder(self.pack)
        for name in [MANIFEST,MANIFEST.upper()]:
            with self.subTest(name=name),self.assertRaises(LibraryError):encode_files({**files,name:b'old'})

    def test_file_count_and_budgets_fail_before_destination(self):
        files=read_folder(self.pack)
        with self.assertRaises(LibraryError):encode_files({**files,'oversize.bin':b'x'*(MAX_FILE+1)})
        with self.assertRaises(LibraryError):encode_files({**files,'a.bin':b'x'*MAX_FILE,'b.bin':b'y'*MAX_FILE})
        with self.assertRaises(LibraryError):encode_files({**files,**{f'extra-{i}':b'' for i in range(MAX_FILES)}})

    def test_destination_cannot_replace_data_or_live_inside_source(self):
        export_pack(self.pack,self.archive)
        with self.assertRaises(FileExistsError):export_pack(self.pack,self.archive)
        target=self.root/'existing';target.mkdir();(target/'keep').write_text('keep')
        with self.assertRaises(LibraryError):import_pack(self.archive,target)
        self.assertEqual((target/'keep').read_text(),'keep')
        with self.assertRaises(LibraryError):export_pack(self.pack,self.pack/'inside.zip')

    def test_wrong_archive_pin_corruption_truncation_and_extra_tail(self):
        raw=encode_files(read_folder(self.pack))
        with self.assertRaisesRegex(LibraryError,'digest mismatch'):decode_files(raw,'0'*64)
        for bad in [raw[:-1],raw+b'junk',raw[:30]+b'X'+raw[31:],b'',raw[:22]]:
            with self.subTest(length=len(bad)),self.assertRaises(LibraryError):decode_files(bad)

    def test_unsupported_zip_flags_offsets_lengths_and_link_modes(self):
        raw=encode_files(read_folder(self.pack));central=struct.unpack_from('<I',raw,len(raw)-6)[0]
        for offset,fmt,value in [(central+8,'H',0x801),(central+10,'H',8),(central+38,'I',0o120777<<16),(central+42,'I',1),(central+24,'I',MAX_FILE+1),(central+30,'H',1),(central+32,'H',1)]:
            bad=bytearray(raw);struct.pack_into('<'+fmt,bad,offset,value)
            with self.subTest(offset=offset),self.assertRaises(LibraryError):decode_files(bytes(bad))

    def test_matching_crc_does_not_hide_inventory_tamper(self):
        raw=bytearray(encode_files(read_folder(self.pack)))
        central=struct.unpack_from('<I',raw,len(raw)-6)[0]
        name_size=struct.unpack_from('<H',raw,26)[0];length=struct.unpack_from('<I',raw,22)[0]
        start=30+name_size
        # Alter a digest in the manifest and repair both CRC fields.
        pos=raw.index(b'"sha256":"',start,start+length)+len(b'"sha256":"')
        raw[pos]=ord('0') if raw[pos]!=ord('0') else ord('1')
        crc=zlib.crc32(raw[start:start+length]);struct.pack_into('<I',raw,14,crc);struct.pack_into('<I',raw,central+16,crc)
        with self.assertRaisesRegex(LibraryError,'inventory or digest'):decode_files(bytes(raw))

    def test_failed_write_leaves_no_import_or_export(self):
        export_pack(self.pack,self.archive)
        with patch('prim_library.transfer.write_new',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):import_pack(self.archive,self.root/'failed')
        self.assertFalse((self.root/'failed').exists())
        self.assertFalse(list(self.root.glob('.prim-transfer-*')))

    def test_real_typescript_exchange_and_byte_identical_encoder(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable; mandatory cross-language CI installs Node')
        py_result=export_pack(self.pack,self.archive)
        script=self.root/'exchange.mjs'
        module=(ROOT/'sdk/typescript/src/pack-transfer.ts').as_uri()
        script.write_text(f"import {{importCompletePack,exportCompletePack}} from {json.dumps(module)};\n"
                          "const [a,d,z,h]=process.argv.slice(2);await importCompletePack(a,d,h);console.log(JSON.stringify(await exportCompletePack(d,z)));\n")
        result=subprocess.run([node,'--experimental-strip-types',str(script),str(self.archive),str(self.root/'ts-copy'),str(self.root/'ts.zip'),py_result['archive_sha256']],capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.archive.read_bytes(),(self.root/'ts.zip').read_bytes())
        shutil.rmtree(self.pack)
        import_pack(self.root/'ts.zip',self.root/'back')
        self.assertEqual(check_capture(self.library,self.root/'back',self.receipt)['status'],'passed')
