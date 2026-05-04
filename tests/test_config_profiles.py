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

    def test_unknown_profile_raises_value_error(self):
        config_path = self._write_config("""[OmeroServer:eu]\nomero.username=u\nomero.password=p\nomero.host=h\nomero.port=4064\nomero.group=g""")
        with self.assertRaises(ValueError) as exc:
            get_omero_config(config_path, server_profile="missing")
        self.assertIn("Unknown OMERO server profile", str(exc.exception))

    def test_missing_keys_raises(self):
        config_path = self._write_config("""[OmeroServer:eu]\nomero.username=u\nomero.host=h\nomero.port=4064\nomero.group=g""")
        with self.assertRaises(ValueError) as exc:
            get_omero_config(config_path, server_profile="eu")
        self.assertIn("missing required", str(exc.exception))

    def test_group_is_required(self):
        config_path = self._write_config("""[OmeroServer:eu]\nomero.username=u\nomero.password=p\nomero.host=h\nomero.port=4064""")
        with self.assertRaises(ValueError) as exc:
            get_omero_config(config_path, server_profile="eu")
        self.assertIn("omero.group", str(exc.exception))

    def test_invalid_port_raises(self):
        config_path = self._write_config("""[OmeroServer:eu]\nomero.username=u\nomero.password=p\nomero.host=h\nomero.port=abc\nomero.group=g""")
        with self.assertRaises(ValueError):
            get_omero_config(config_path, server_profile="eu")

    def test_section_style_profile_success(self):
        config_path = self._write_config("""[OmeroServer:eu]\nomero.username=u\nomero.password=p\nomero.host=h\nomero.port=4064\nomero.group=lab-a""")
        username, password, host, port, group = get_omero_config(config_path, server_profile="eu")
        self.assertEqual((username, password, host, port, group), ("u", "p", "h", 4064, "lab-a"))


if __name__ == "__main__":
    unittest.main()
