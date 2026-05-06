import json
import unittest
from unittest.mock import patch

from typer.testing import CliRunner

from omero_bifrost.cli import app, _emit_execution_output
from omero_bifrost.utils.omero_cli_runner import CommandResult


class TestCliOutputSchema(unittest.TestCase):
    def test_emit_execution_output_profiles_map_shape(self):
        with patch("omero_bifrost.cli.print") as mock_print:
            _emit_execution_output([{"id": "1"}, {"id": "2"}], profile="eu")

        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["profiles"]["eu"]["status"], "ok")
        self.assertEqual(payload["profiles"]["eu"]["count"], 2)

    @patch("omero_bifrost.cli.get_omero_config", return_value=("u", "p", "h", 4064, "g"))
    @patch("omero_bifrost.cli.omero_connect")
    @patch("omero_bifrost.cli.export_ome_tiff_file", return_value=CommandResult(0, "ok", "", ["omero"]))
    def test_pull_ome_tiffs_supports_json_file_output(self, _mock_export, mock_connect, _mock_cfg):
        conn = mock_connect.return_value
        conn.getObject.return_value = type("Img", (), {"getName": lambda self: "imgA"})()

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["pull", "ome-tiffs", "./out", "--img-id", "7", "--to-file", "--output", "pull.json"])
            self.assertEqual(result.exit_code, 0)
            with open("pull.json", "r", encoding="utf-8") as handle:
                payload = json.load(handle)

        self.assertIn("records", payload)
        self.assertEqual(payload["profiles"]["default"]["status"], "ok")

    @patch("omero_bifrost.cli.get_omero_config", return_value=("u", "p", "h", 4064, "g"))
    @patch("omero_bifrost.cli.omero_connect")
    @patch("omero_bifrost.cli.download_original_image_file", return_value=CommandResult(0, "ok", "", ["omero"]))
    def test_pull_orig_files_console_json_shape(self, _mock_download, mock_connect, _mock_cfg):
        file_obj = type("Orig", (), {"getId": lambda self: 22, "getName": lambda self: "raw.czi"})()
        fileset = type("Fs", (), {"listFiles": lambda self: [file_obj]})()
        image = type("Img", (), {"getFileset": lambda self: fileset})()
        conn = mock_connect.return_value
        conn.getObject.return_value = image

        runner = CliRunner()
        result = runner.invoke(app, ["pull", "orig-files", "./out", "--img-id", "9"])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["profiles"]["default"]["status"], "ok")

    def test_no_xml_flag_label_in_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["query", "list-all", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("to-xml", result.stdout)


if __name__ == "__main__":
    unittest.main()
