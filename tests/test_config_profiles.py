import tempfile
import unittest
from pathlib import Path

from omero_bifrost.utils.util_ops import get_omero_config


class TestConfigProfiles(unittest.TestCase):
    def _write_config(self, content: str) -> str:
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        config_path = Path(tmp_dir.name) / "imaging_config.properties"
        config_path.write_text(content)
        return str(config_path)

    def test_legacy_default_profile_is_used_when_not_provided(self):
        config_path = self._write_config(
            """
[OmeroServerSection]
omero.username = legacy-user
omero.password = legacy-pass
omero.host = legacy-host
omero.port = 4064
""".strip()
        )

        username, password, host, port, group = get_omero_config(config_path)

        self.assertEqual(username, "legacy-user")
        self.assertEqual(password, "legacy-pass")
        self.assertEqual(host, "legacy-host")
        self.assertEqual(port, 4064)
        self.assertIsNone(group)

    def test_named_server_profile_is_used_when_selected(self):
        config_path = self._write_config(
            """
[OmeroServerSection]
omero.username = legacy-user
omero.password = legacy-pass
omero.host = legacy-host
omero.port = 4064

[secondary]
omero.username = prof-user
omero.password = prof-pass
omero.host = prof-host
omero.port = 14064
omero.group = lab-a
""".strip()
        )

        username, password, host, port, group = get_omero_config(config_path, server_profile="secondary")

        self.assertEqual(username, "prof-user")
        self.assertEqual(password, "prof-pass")
        self.assertEqual(host, "prof-host")
        self.assertEqual(port, 14064)
        self.assertEqual(group, "lab-a")

    def test_unknown_profile_raises_value_error(self):
        config_path = self._write_config(
            """
[OmeroServerSection]
omero.username = legacy-user
omero.password = legacy-pass
omero.host = legacy-host
omero.port = 4064
""".strip()
        )

        with self.assertRaises(ValueError) as exc:
            get_omero_config(config_path, server_profile="missing-profile")

        self.assertIn("Unknown OMERO server profile", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
