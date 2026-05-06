import tempfile
import unittest
from pathlib import Path

from omero_bifrost.federation.runner import FederationRunner, FederationRecord


class TestFederationRunner(unittest.TestCase):
    def test_deterministic_ordering(self):
        runner = FederationRunner(max_workers=2)

        def fn(profile):
            return [
                FederationRecord(server_profile=profile, server_host=profile, operation="query", status="ok", local_object_id="2", message="ok"),
                FederationRecord(server_profile=profile, server_host=profile, operation="query", status="ok", local_object_id="1", message="ok"),
            ]

        out1 = runner.run(["b", "a"], "query", fn)
        out2 = runner.run(["a", "b"], "query", fn)
        self.assertEqual([(r.server_profile, r.local_object_id) for r in out1["records"]], [(r.server_profile, r.local_object_id) for r in out2["records"]])

    def test_repeated_concurrency_schema_stable(self):
        runner = FederationRunner(max_workers=4)

        def fn(profile):
            return [FederationRecord(server_profile=profile, server_host=profile, operation="push", status="ok", local_object_id="1", message="ok")]

        shapes = []
        for _ in range(5):
            out = runner.run(["c", "b", "a"], "push", fn)
            shapes.append([(r.server_profile, r.operation, r.provenance_id is not None) for r in out["records"]])
        self.assertTrue(all(s == shapes[0] for s in shapes[1:]))

    def test_partial_failure_categories_and_summary(self):
        runner = FederationRunner(fail_policy="continue")

        def fn(profile):
            if profile == "b":
                raise PermissionError("bad auth")
            return [FederationRecord(server_profile=profile, server_host=profile, operation="query", status="ok", message="ok")]

        out = runner.run(["a", "b"], "query", fn)
        self.assertEqual(out["profiles"]["b"]["error_category"], "auth")
        err = [r for r in out["records"] if r.server_profile == "b"][0]
        self.assertEqual(err.error_category, "auth")

    def test_provenance_completeness_and_checksums(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.tsv"
            p.write_text("a\tb\n", encoding="utf-8")
            runner = FederationRunner()
            out = runner.run(["a"], "pull", lambda prof: [FederationRecord(server_profile=prof, server_host=prof, operation="pull", status="ok", message="ok")], args={"password": "secret", "x": "1"}, input_artifacts=[str(p)])
            prov = out["provenance"]
            self.assertIn(str(p), prov.input_checksums)
            self.assertEqual(prov.sanitized_args["password"], "***")
            self.assertTrue(all(r.provenance_id == prov.provenance_id for r in out["records"]))


if __name__ == "__main__":
    unittest.main()
