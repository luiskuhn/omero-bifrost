import unittest

from omero_bifrost.federation.layer import PullTarget, federated_query, federated_push, federated_annotate, federated_pull
from omero_bifrost.federation.runner import FederationRecord


class TestFederatedLayer(unittest.TestCase):
    def test_federated_query_runs_all_profiles(self):
        out = federated_query(["us", "eu"], lambda p: [FederationRecord(server_profile=p, server_host=p, operation="query", status="ok")])
        self.assertEqual(sorted(out["profiles"].keys()), ["eu", "us"])

    def test_federated_push_selected_subset(self):
        out = federated_push(["eu"], lambda p: [FederationRecord(server_profile=p, server_host=p, operation="push", status="ok")])
        self.assertEqual(list(out["profiles"].keys()), ["eu"])

    def test_federated_annotate_scale(self):
        out = federated_annotate(["eu", "us"], lambda p: [FederationRecord(server_profile=p, server_host=p, operation="annotate", status="ok", local_object_id="1")])
        self.assertEqual(len(out["records"]), 2)

    def test_federated_pull_profile_per_target(self):
        targets = [PullTarget("eu", "11", "image"), PullTarget("us", "22", "image")]

        def pull_fn(t):
            return [FederationRecord(server_profile=t.server_profile, server_host=t.server_profile, operation="pull", status="ok", local_object_id=t.target_id)]

        out = federated_pull(targets, pull_fn)
        ids = sorted(r.local_object_id for r in out["records"])
        self.assertEqual(ids, ["11", "22"])


if __name__ == "__main__":
    unittest.main()
