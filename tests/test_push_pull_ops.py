import unittest
from unittest.mock import patch

from omero_bifrost.pull.pull_ops import export_ome_tiff_file
from omero_bifrost.push.push_ops import (
    attach_file_to_image,
    register_image_file_with_dataset_id,
    register_image_folder_with_dataset_id,
)
from omero_bifrost.utils.omero_cli_runner import CommandResult


class TestPushPullOps(unittest.TestCase):
    @patch("omero_bifrost.push.push_ops.run_omero_cli")
    def test_register_image_file_includes_import_performance_flags(self, mock_run):
        mock_run.return_value = CommandResult(0, "Image:11", "", ["omero", "import"])

        image_ids = register_image_file_with_dataset_id("/tmp/file.tiff", 1, "u", "p", "h")

        self.assertEqual(image_ids, ["11"])
        passed_cmd = mock_run.call_args.args[0]
        self.assertIn("--skip", passed_cmd)
        self.assertIn("all", passed_cmd)
        self.assertIn("-C", passed_cmd)
        self.assertIn("--parallel-upload", passed_cmd)
        self.assertIn("128", passed_cmd)

    @patch("omero_bifrost.push.push_ops.run_omero_cli")
    def test_register_image_folder_includes_import_performance_flags(self, mock_run):
        mock_run.return_value = CommandResult(0, "Image:12", "", ["omero", "import"])

        image_ids = register_image_folder_with_dataset_id("/tmp/folder", 1, "u", "p", "h")

        self.assertEqual(image_ids, ["12"])
        passed_cmd = mock_run.call_args.args[0]
        self.assertIn("--skip", passed_cmd)
        self.assertIn("all", passed_cmd)
        self.assertIn("-C", passed_cmd)
        self.assertIn("--parallel-upload", passed_cmd)
        self.assertIn("128", passed_cmd)

    @patch("omero_bifrost.push.push_ops.run_omero_cli")
    def test_attach_file_to_image_parses_annotation_path(self, mock_run):
        mock_run.side_effect = [
            CommandResult(0, "OriginalFile:100", "", ["omero"]),
            CommandResult(0, "FileAnnotation:200", "", ["omero"]),
            CommandResult(0, "ImageAnnotationLink:300", "", ["omero"]),
        ]

        link_id = attach_file_to_image("/tmp/file.txt", 1, "u", "p", "h")
        self.assertEqual(link_id, "300")

    @patch("omero_bifrost.pull.pull_ops.run_omero_cli")
    def test_export_ome_tiff_adds_extension(self, mock_run):
        mock_run.return_value = CommandResult(0, "done", "", ["omero", "export"])

        result = export_ome_tiff_file(5, "/tmp/out", "u", "p", "h")

        self.assertEqual(result.stdout, "done")
        passed_cmd = mock_run.call_args.args[0]
        self.assertIn("/tmp/out.ome.tiff", passed_cmd)


if __name__ == "__main__":
    unittest.main()
