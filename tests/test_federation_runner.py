import unittest
from omero_bifrost.federation.runner import FederationRunner, FederationRecord


class TestFederationRunner(unittest.TestCase):
    def test_deterministic_ordering(self):
        runner = FederationRunner(max_workers=2)
        def fn(profile):
            return [FederationRecord(server_profile=profile, server_host=profile, operation="query", status="ok", local_object_id="2"), FederationRecord(server_profile=profile, server_host=profile, operation="query", status="ok", local_object_id="1")]
        out1 = runner.run(["b", "a"], "query", fn)
        out2 = runner.run(["a", "b"], "query", fn)
        self.assertEqual([r.local_object_id for r in out1["records"]], [r.local_object_id for r in out2["records"]])

    def test_fail_policy_continue(self):
        runner = FederationRunner(fail_policy="continue")
        def fn(profile):
            if profile == "b":
                raise RuntimeError("boom")
            return [FederationRecord(server_profile=profile, server_host=profile, operation="query", status="ok")]
        out = runner.run(["a", "b"], "query", fn)
        self.assertIn("a", out["profiles"])
        self.assertIn("b", out["profiles"])


if __name__ == "__main__":
    unittest.main()
