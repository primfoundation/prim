import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from opf.validate import validate_pack

EXAMPLE = Path(__file__).parents[1] / "examples" / "v1-product"


def rules(reports):
    return {problem.rule for report in reports for problem in report.problems}


class ValidatorTests(unittest.TestCase):
    def copy_example(self, directory):
        root = Path(directory) / "pack"
        shutil.copytree(EXAMPLE, root)
        return root

    def test_reference_pack_is_valid(self):
        self.assertFalse(validate_pack(EXAMPLE)[0].errors)

    def test_v0_markdown_pack_is_not_accepted(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.md").write_text("---\nopf_version: 0.2.6\n---\n")
            self.assertIn("model_missing", rules(validate_pack(root)))

    def test_relationship_direction_is_typed(self):
        with TemporaryDirectory() as directory:
            root = self.copy_example(directory)
            model = json.loads((root / "product.json").read_text())
            rel = next(r for r in model["relationships"] if r["type"] == "expresses")
            rel["from"], rel["to"] = rel["to"], rel["from"]
            (root / "product.json").write_text(json.dumps(model))
            self.assertIn("relationship_types", rules(validate_pack(root)))

    def test_hierarchy_requires_one_ordered_parent(self):
        with TemporaryDirectory() as directory:
            root = self.copy_example(directory)
            model = json.loads((root / "product.json").read_text())
            model["relationships"] = [r for r in model["relationships"] if r["to"] != "opf:sample:intent"]
            (root / "product.json").write_text(json.dumps(model))
            found = rules(validate_pack(root))
            self.assertIn("hierarchy_parent", found)
            self.assertIn("hierarchy_reachability", found)

    def test_every_entity_requires_one_created_event(self):
        with TemporaryDirectory() as directory:
            root = self.copy_example(directory)
            model = json.loads((root / "product.json").read_text())
            model["events"] = [e for e in model["events"] if "opf:sample:intent" not in e["subjects"]]
            (root / "product.json").write_text(json.dumps(model))
            self.assertIn("created_event", rules(validate_pack(root)))

    def test_acceptance_targets_decisions(self):
        with TemporaryDirectory() as directory:
            root = self.copy_example(directory)
            model = json.loads((root / "product.json").read_text())
            model["events"].append({
                "id": "opf:sample:event:bad-acceptance", "type": "accepted",
                "at": "2026-08-08T00:10:00Z", "subjects": ["opf:sample:intent"],
                "actor": "human:test", "detail": "Wrong target",
            })
            (root / "product.json").write_text(json.dumps(model))
            self.assertIn("accepted_event", rules(validate_pack(root)))


if __name__ == "__main__":
    unittest.main()
