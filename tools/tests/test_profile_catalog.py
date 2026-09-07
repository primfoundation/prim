from __future__ import annotations

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from profile_catalog import (MANIFEST, MAX_BYTES, ProfileError, discover_profiles,
                             encode, inspect_profile, main)
import yaml


class ProfileCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = {
            "format": "prim-profile", "manifest_version": "0.1",
            "id": "example/research", "name": "Research", "version": "1.2.3",
            "maturity": "development", "description": "A test profile.",
        }

    def tearDown(self):
        self.temp.cleanup()

    def package(self, name="one", data=None, body="# Profile\n\nAn inspectable definition.\n"):
        folder = self.root / name
        folder.mkdir(parents=True, exist_ok=True)
        content = "---\n" + yaml.safe_dump(self.data if data is None else data, sort_keys=False) + "---\n" + body
        (folder / MANIFEST).write_text(content, encoding="utf-8")
        return folder

    def test_repository_is_not_required(self):
        item = inspect_profile(self.package())
        self.assertEqual(item["metadata"]["id"], "example/research")
        self.assertNotIn("repo", item["metadata"])

    def test_moving_a_package_preserves_identity_and_manifest_hash(self):
        source = self.package()
        before = inspect_profile(source)
        destination = self.root / "some-other-repository" / "renamed-folder"
        shutil.copytree(source, destination)
        self.assertEqual(before, inspect_profile(destination))

    def test_discovery_multiple_profiles_and_versions(self):
        self.package("nested/one")
        newer = dict(self.data, version="2.0.0")
        self.package("nested/two", newer)
        other = dict(self.data, id="other/research")
        self.package("elsewhere/three", other)
        found = discover_profiles(self.root)
        self.assertEqual(len(found["profiles"]), 3)
        self.assertEqual(found, discover_profiles(self.root))
        self.assertNotIn(str(self.root), encode(found))

    def test_duplicate_identity_version_is_rejected(self):
        self.package("one")
        self.package("two")
        with self.assertRaisesRegex(ProfileError, "duplicate profile"):
            discover_profiles(self.root)

    def test_package_is_a_discovery_boundary(self):
        self.package("one")
        self.package("one/examples/demo")
        self.assertEqual(len(discover_profiles(self.root)["profiles"]), 1)

    def test_dependency_folders_are_not_scanned(self):
        self.package("one")
        self.package("node_modules/not-published")
        self.assertEqual(len(discover_profiles(self.root)["profiles"]), 1)

    def test_no_packages_is_not_a_successful_empty_catalog(self):
        (self.root / "SPEC.md").write_text("Legacy profile, not migrated.")
        with self.assertRaisesRegex(ProfileError, "no PROFILE"):
            discover_profiles(self.root)

    def test_resource_paths_can_be_files_or_directories(self):
        data = dict(self.data, resources={"specification": "SPEC.md", "examples": "examples"})
        folder = self.package(data=data)
        (folder / "SPEC.md").write_text("# Spec")
        (folder / "examples").mkdir()
        self.assertEqual(inspect_profile(folder)["checks"]["declared_resource_paths"], "passed")

    def test_noncontained_resource_paths_fail(self):
        for value in ("../secret", "/tmp/secret", "https://example.test/a", "C:\\secret",
                      "a/../secret", "./SPEC.md", "a//b", "a/", "a\x00b", "a\nb", "a:b"):
            with self.subTest(path=value):
                folder = self.package(data=dict(self.data, resources={"specification": value}))
                with self.assertRaises(ProfileError):
                    inspect_profile(folder)

    def test_missing_resource_fails(self):
        folder = self.package(data=dict(self.data, resources={"specification": "missing.md"}))
        with self.assertRaisesRegex(ProfileError, "missing"):
            inspect_profile(folder)

    def test_symlink_resource_fails(self):
        folder = self.package(data=dict(self.data, resources={"specification": "link.md"}))
        outside = self.root / "outside.md"
        outside.write_text("private")
        (folder / "link.md").symlink_to(outside)
        with self.assertRaisesRegex(ProfileError, "symlink"):
            inspect_profile(folder)

    def test_symlink_manifest_and_roots_fail(self):
        folder = self.package()
        linked = self.root / "linked"
        linked.symlink_to(folder, target_is_directory=True)
        for target in (linked, linked / MANIFEST):
            with self.subTest(target=str(target)):
                with self.assertRaisesRegex(ProfileError, "symlink"):
                    inspect_profile(target)
        with self.assertRaisesRegex(ProfileError, "symlink"):
            discover_profiles(linked)
        manifest = folder / MANIFEST
        manifest.rename(folder / "original.md")
        manifest.symlink_to(folder / "original.md")
        with self.assertRaisesRegex(ProfileError, "symlink"):
            inspect_profile(folder)

    def test_symlink_directory_in_source_is_not_silently_followed(self):
        self.package()
        (self.root / "external").symlink_to(self.root / "one", target_is_directory=True)
        with self.assertRaisesRegex(ProfileError, "symlink"):
            discover_profiles(self.root)

    def test_malformed_unsupported_duplicate_and_unsafe_yaml_fail(self):
        bad_headers = [
            "id: one\nid: two", "x: &x [*x]", "x: !!python/object/apply:os.system ['false']",
            "[one, two]", "x: [unclosed", "extensions:\n  a: 1\n  a: 2",
            "extensions:\n  7: wrong", "extensions:\n  date: 2026-09-06",
            "extensions:\n  n: .nan", "extensions:\n  <<: {a: 1}",
        ]
        folder = self.package()
        for header in bad_headers:
            with self.subTest(header=header):
                (folder / MANIFEST).write_text(f"---\n{header}\n---\n# Body\n")
                with self.assertRaises(ProfileError):
                    inspect_profile(folder)

    def test_unframed_empty_or_unclosed_document_fails(self):
        folder = self.package()
        for raw in ("# no frontmatter", "---\nid: foo\n", "---\n{}\n---\n", "---\n---\nBody"):
            with self.subTest(raw=raw):
                (folder / MANIFEST).write_text(raw)
                with self.assertRaises(ProfileError):
                    inspect_profile(folder)

    def test_invalid_fields_are_rejected_not_coerced(self):
        mutations = [{"format": "other"}, {"manifest_version": 0.1}, {"id": "research"},
                     {"id": "GitHub/research"}, {"id": "example/../x"}, {"version": 1.2},
                     {"name": " "}, {"description": "x" * 1025}, {"maturity": "excellent"},
                     {"kinds": "investigation"}, {"kinds": ["x", "x"]},
                     {"legacy_aliases": [True]}, {"resources": []}, {"extensions": []},
                     {"repo": "required-no-more"}, {"description": "tab\tinjected"}]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ProfileError):
                    inspect_profile(self.package(data=dict(self.data, **mutation)))

    def test_strict_semantic_versions(self):
        for version in ("0.1.0", "1.2.3-dev.1", "1.0.0+build.7", "1.0.0-rc.1+abc"):
            inspect_profile(self.package(data=dict(self.data, version=version)))
        for version in ("1.2", "01.2.3", "1.2.3-01", "^1.2.3", "latest", "1.2.3-", "1.2.3+", "1.2.3٤"):
            with self.subTest(version=version):
                with self.assertRaises(ProfileError):
                    inspect_profile(self.package(data=dict(self.data, version=version)))

    def test_size_encoding_and_nesting_limits(self):
        folder = self.package()
        for raw in (b"x" * (MAX_BYTES + 1), b"\xff", ("---\nx: " + "[" * 40 + "0" + "]" * 40 + "\n---\nBody").encode()):
            (folder / MANIFEST).write_bytes(raw)
            with self.assertRaises(ProfileError):
                inspect_profile(folder)

    def test_discovery_limits_do_not_return_partial_success(self):
        self.package("a/b/c")
        for kwargs in ({"max_depth": 1}, {"max_entries": 1}, {"max_depth": -1}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ProfileError):
                    discover_profiles(self.root, **kwargs)

    def test_declared_validator_is_never_executed(self):
        folder = self.package(data=dict(self.data, resources={"validator": "evil.py"}))
        marker = folder / "executed"
        (folder / "evil.py").write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        item = inspect_profile(folder)
        self.assertFalse(marker.exists())
        self.assertEqual(item["checks"]["profile_conformance"], "not_checked")
        self.assertEqual(item["checks"]["publisher_identity"], "not_verified")
        self.assertEqual(item["checks"]["security_review"], "not_performed")

    def test_extensions_and_aliases_are_metadata_not_authority(self):
        data = dict(self.data, legacy_aliases=["orf"], extensions={"example": {"key": [1, "two", None]}})
        item = inspect_profile(self.package(data=data))
        self.assertEqual(item["metadata"], data)
        self.assertEqual(item["checks"]["publisher_identity"], "not_verified")

    def test_manifest_digest_does_not_claim_resource_integrity(self):
        data = dict(self.data, resources={"specification": "SPEC.md"})
        folder = self.package(data=data)
        (folder / "SPEC.md").write_text("before")
        before = inspect_profile(folder)["manifest_sha256"]
        (folder / "SPEC.md").write_text("after")
        self.assertEqual(before, inspect_profile(folder)["manifest_sha256"])

    def test_catalog_cli_and_drift_detection(self):
        self.package()
        target = self.root / "catalog.json"
        self.assertEqual(main(["discover", str(self.root), "--output", str(target)]), 0)
        self.assertEqual(main(["discover", str(self.root), "--check", str(target)]), 0)
        target.write_text("{}\n")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["discover", str(self.root), "--check", str(target)]), 1)

    def test_cli_diagnostics_are_nonzero_without_traceback(self):
        with contextlib.redirect_stderr(io.StringIO()) as output:
            result = main(["inspect", str(self.root / "missing")])
        self.assertEqual(result, 1)
        self.assertNotIn("Traceback", output.getvalue())

    def test_invalid_sources_and_outputs_are_rejected(self):
        folder = self.package()
        with self.assertRaises(ProfileError):
            discover_profiles(folder / MANIFEST)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["inspect", str(folder), "--output", str(folder / MANIFEST)]), 1)

    def test_repository_research_example_is_only_manifest_checked(self):
        root = Path(__file__).resolve().parents[2]
        item = inspect_profile(root / "profiles/research")
        self.assertEqual(item["metadata"]["id"], "primfoundation/research")
        self.assertEqual(item["checks"]["profile_conformance"], "not_checked")


if __name__ == "__main__":
    unittest.main()
