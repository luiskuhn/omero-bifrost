import unittest
from unittest.mock import patch

from omero_bifrost.utils.omero_cli_runner import (
    CommandResult,
    OmeroCliCommandError,
    OmeroCliParseError,
    parse_file_annotation_id,
    parse_image_annotation_link_id,
    parse_image_ids,
    parse_original_file_id,
    parse_tag_annotation_id,
    run_omero_cli,
)


class TestRunnerAndParsers(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_omero_cli_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "ok"
        mock_run.return_value.stderr = ""

        result = run_omero_cli(["omero", "import", "-w", "secret"])

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.cmd[-1], "***")

    @patch("subprocess.run")
    def test_run_omero_cli_error_maps_to_exception(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "boom"

        with self.assertRaises(OmeroCliCommandError) as ctx:
            run_omero_cli(["omero", "export"])

        self.assertEqual(ctx.exception.result.stderr, "boom")

    def test_parse_known_prefixes(self):
        result = CommandResult(
            returncode=0,
            stdout="\n".join([
                "Image:11,12",
                "OriginalFile:22",
                "TagAnnotation:33",
                "FileAnnotation:44",
                "ImageAnnotationLink:55",
            ]),
            stderr="",
            cmd=["omero"],
        )

        self.assertEqual(parse_image_ids(result), ["11", "12"])
        self.assertEqual(parse_original_file_id(result), "22")
        self.assertEqual(parse_tag_annotation_id(result), 33)
        self.assertEqual(parse_file_annotation_id(result), "44")
        self.assertEqual(parse_image_annotation_link_id(result), "55")

    def test_parse_missing_prefix_raises(self):
        result = CommandResult(returncode=0, stdout="nothing", stderr="", cmd=["omero"])
        with self.assertRaises(OmeroCliParseError):
            parse_image_ids(result)


if __name__ == "__main__":
    unittest.main()
