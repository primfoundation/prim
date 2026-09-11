from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from program import PlanError, main, read_plan, render, validate_plan


class ProgramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "program").mkdir()
        (self.root / "evidence.md").write_text("Test-only evidence fixture, not production proof.")
        self.plan = {
            "format_version": 1, "program": "Test", "mission": "Keep obligations visible.", "as_of": "2026-09-06",
            "execution": {"state": "test", "target_repository": "example/repo", "base_commit": "a" * 40,
                          "target_branch": "test", "background_jobs": "none"},
            "workstreams": [{"id": "W", "name": "Work", "delivery": "foundation"}],
            "milestones": [{"id": "M0", "name": "First", "gate": "Evidence is reviewed."}],
            "evidence": [{"id": "E1", "stage": "tests", "path": "evidence.md", "summary": "A fixture."}],
            "requirements": [{"id": "W-001", "workstream": "W", "title": "Test", "acceptance": "Pass a test.",
                              "milestone": "M0", "status": "planned", "owner": "test-owner", "depends_on": [],
                              "required_evidence": ["tests"], "evidence": [], "note": ""}],
            "life_domains": ["household"], "coverage_lenses": ["offline"],
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_ledger(self):
        validate_plan(self.plan, self.root)

    def test_complete_requires_declared_evidence(self):
        self.plan["requirements"][0]["status"] = "complete"
        with self.assertRaisesRegex(PlanError, "without required evidence"):
            validate_plan(self.plan, self.root)
        self.plan["requirements"][0]["evidence"] = ["E1"]
        validate_plan(self.plan, self.root)

    def test_tests_do_not_satisfy_release_or_real_use(self):
        row = self.plan["requirements"][0]
        row.update(status="complete", evidence=["E1"], required_evidence=["tests", "deployment", "real_use"])
        with self.assertRaisesRegex(PlanError, "required evidence"):
            validate_plan(self.plan, self.root)

    def test_duplicates_fail(self):
        for key in ("workstreams", "requirements", "milestones", "evidence"):
            with self.subTest(key=key):
                plan = copy.deepcopy(self.plan)
                plan[key].append(copy.deepcopy(plan[key][0]))
                with self.assertRaisesRegex(PlanError, "duplicate"):
                    validate_plan(plan, self.root)

    def test_uncovered_workstream_or_milestone_fails(self):
        for key in ("workstreams", "milestones"):
            with self.subTest(key=key):
                plan = copy.deepcopy(self.plan)
                extra = dict(plan[key][0], id="UNUSED")
                plan[key].append(extra)
                with self.assertRaisesRegex(PlanError, "uncovered"):
                    validate_plan(plan, self.root)

    def test_unknown_references_fail(self):
        for key, value in (("workstream", "BAD"), ("milestone", "BAD"), ("depends_on", ["BAD"]),
                           ("evidence", ["BAD"]), ("required_evidence", ["looks-good"])):
            with self.subTest(key=key):
                plan = copy.deepcopy(self.plan)
                plan["requirements"][0][key] = value
                with self.assertRaises(PlanError):
                    validate_plan(plan, self.root)

    def test_cycle_fails(self):
        self.plan["requirements"][0]["depends_on"] = ["W-001"]
        with self.assertRaisesRegex(PlanError, "cycle"):
            validate_plan(self.plan, self.root)

    def test_indirect_cycle_fails(self):
        first = self.plan["requirements"][0]
        second = dict(first, id="W-002", depends_on=["W-001"])
        first["depends_on"] = ["W-002"]
        self.plan["requirements"].append(second)
        with self.assertRaisesRegex(PlanError, "cycle"):
            validate_plan(self.plan, self.root)

    def test_completed_work_cannot_have_incomplete_dependencies(self):
        first = self.plan["requirements"][0]
        self.plan["requirements"].append(dict(first, id="W-002", status="complete", evidence=["E1"], depends_on=["W-001"]))
        with self.assertRaisesRegex(PlanError, "unfinished dependencies"):
            validate_plan(self.plan, self.root)

    def test_blocked_requires_reason(self):
        self.plan["requirements"][0]["status"] = "blocked"
        with self.assertRaisesRegex(PlanError, "without a reason"):
            validate_plan(self.plan, self.root)

    def test_missing_or_escaping_evidence_fails(self):
        for path in ("missing.md", "../evidence.md", "/tmp/evidence.md", "https://example.test/proof"):
            with self.subTest(path=path):
                plan = copy.deepcopy(self.plan)
                plan["evidence"][0]["path"] = path
                with self.assertRaises(PlanError):
                    validate_plan(plan, self.root)

    def test_missing_acceptance_owner_status_or_evidence_requirements_fails(self):
        for key, value in (("acceptance", ""), ("owner", ""), ("status", "shipped-ish"), ("required_evidence", [])):
            with self.subTest(key=key):
                plan = copy.deepcopy(self.plan)
                plan["requirements"][0][key] = value
                with self.assertRaises(PlanError):
                    validate_plan(plan, self.root)

    def test_empty_report_does_not_count_as_retained_evidence(self):
        (self.root / "evidence.md").write_bytes(b"")
        with self.assertRaisesRegex(PlanError, "evidence file empty"):
            validate_plan(self.plan, self.root)

    def test_loss_of_domain_coverage_fails(self):
        for key in ("life_domains", "coverage_lenses"):
            plan = copy.deepcopy(self.plan)
            plan[key] = []
            with self.assertRaises(PlanError):
                validate_plan(plan, self.root)

    def test_duplicate_json_keys_fail(self):
        (self.root / "program/plan.json").write_text('{"format_version":1,"format_version":2}')
        with self.assertRaisesRegex(PlanError, "duplicate JSON"):
            read_plan(self.root)

    def test_render_is_deterministic_and_drift_fails(self):
        (self.root / "program/plan.json").write_text(json.dumps(self.plan))
        self.assertEqual(render(self.plan), render(self.plan))
        self.assertEqual(main(["render", "--root", str(self.root)]), 0)
        self.assertEqual(main(["render", "--root", str(self.root), "--check"]), 0)
        (self.root / "ROADMAP.md").write_text("Everything is done!")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["render", "--root", str(self.root), "--check"]), 1)

    def test_version_must_be_actual_integer(self):
        self.plan["format_version"] = True
        with self.assertRaises(PlanError):
            validate_plan(self.plan, self.root)

    def test_invalid_calendar_date_fails(self):
        self.plan["as_of"] = "2026-99-99"
        with self.assertRaisesRegex(PlanError, "date"):
            validate_plan(self.plan, self.root)

    def test_current_repository_plan(self):
        root = Path(__file__).resolve().parents[2]
        plan = read_plan(root)
        validate_plan(plan, root)
        self.assertTrue(plan["requirements"])
        self.assertEqual(plan["program"], "Prim Foundation")

    def delivery_package(self):
        return {"id": "D95-01", "title": "Keep scope", "owner": "test-owner", "wave": 0,
                "goals": ["G7"], "entry_from": [], "requirements": ["W-001"],
                "entry_gate": "Inputs observed.", "exit_gate": "Scope is preserved."}

    def test_delivery_mapping_cannot_lose_duplicate_or_invent_requirements(self):
        package = self.delivery_package()
        self.plan["delivery_packages"] = [package]
        validate_plan(self.plan, self.root)
        variants = [[], [dict(package, requirements=["W-999"])],
                    [package, dict(package, id="D95-02")]]
        for packages in variants:
            with self.subTest(packages=packages):
                plan = copy.deepcopy(self.plan)
                plan["delivery_packages"] = packages
                with self.assertRaises(PlanError):
                    validate_plan(plan, self.root)
        self.plan["requirements"].append(dict(self.plan["requirements"][0], id="W-002"))
        with self.assertRaisesRegex(PlanError, "every requirement exactly once"):
            validate_plan(self.plan, self.root)

    def test_delivery_dependencies_cannot_be_unknown_or_cyclic(self):
        package = self.delivery_package()
        self.plan["requirements"].append(dict(self.plan["requirements"][0], id="W-002"))
        self.plan["delivery_packages"] = [package, dict(package, id="D95-02",
                                                       requirements=["W-002"], entry_from=["D95-01"])]
        validate_plan(self.plan, self.root)
        for deps in (["D95-99"], ["D95-01"], ["D95-02"]):
            with self.subTest(deps=deps):
                plan = copy.deepcopy(self.plan)
                plan["delivery_packages"][0]["entry_from"] = deps
                with self.assertRaises(PlanError):
                    validate_plan(plan, self.root)

    def test_delivery_packages_cannot_create_parallel_status_authority(self):
        self.plan["delivery_packages"] = [dict(self.delivery_package(), status="complete")]
        with self.assertRaisesRegex(PlanError, "must not duplicate requirement status"):
            validate_plan(self.plan, self.root)


if __name__ == "__main__":
    unittest.main()
