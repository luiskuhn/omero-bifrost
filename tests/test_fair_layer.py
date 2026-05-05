import unittest
import tempfile
from pathlib import Path

from omero_bifrost.utils.filter_expr import parse_filter_expr, FilterParseError
from omero_bifrost.fair.metadata_table import load_metadata_table, expand_rows, MetadataTableError
from omero_bifrost.fair.ontology_normalization import normalize_term
from omero_bifrost.fair.metadata_schema import validate_row


class TestFilterExpr(unittest.TestCase):
    def test_legacy_and_colon_value(self):
        e = parse_filter_expr("k:va:l")
        self.assertEqual(e.key, "k")
        self.assertEqual(e.value, "va:l")

    def test_legacy_maps_to_equality(self):
        e = parse_filter_expr("age:33")
        self.assertEqual(e.op, "=")
        self.assertEqual(e.value, "33")

    def test_error(self):
        with self.assertRaises(FilterParseError):
            parse_filter_expr("bad")


class TestMetadataTable(unittest.TestCase):
    def test_deterministic_expansion(self):
        with tempfile.TemporaryDirectory() as d:
            dpath = Path(d)
            (dpath / "b.tif").write_text("x")
            (dpath / "a.tif").write_text("x")
            tsv = dpath / "m.csv"
            tsv.write_text("IMAGE_DATA_PATH,REMBI_DISEASE\n%s,NCIT:C1\n" % d)
            rows = load_metadata_table(str(tsv))
            expanded = expand_rows(rows)
            self.assertEqual([Path(r.image_path).name for r in expanded], ["a.tif", "b.tif"])

    def test_unresolved_path(self):
        with self.assertRaises(MetadataTableError):
            expand_rows([{"IMAGE_DATA_PATH": "/nope"}])


class TestOntology(unittest.TestCase):
    def test_normalization_equivalence(self):
        self.assertEqual(normalize_term("C123")[0], "NCIT:C123")
        self.assertEqual(normalize_term("NCIT:C123")[0], "NCIT:C123")
        self.assertEqual(normalize_term("http://purl.obolibrary.org/obo/NCIT_C123")[0], "NCIT:C123")

    def test_row_validation(self):
        vals = validate_row({
            "REMBI_EXPERIMENT_ID": "EXP-1",
            "REMBI_ACQUISITION_DATE": "2026-05-05",
            "OME_IMAGE_NAME": "img-1",
            "REMBI_BIOSAMPLE_TYPE": "BADPREFIX:1",
            "OME_PIXEL_SIZE_X_UM": "not-a-number",
        })
        self.assertTrue(any(v.reason_code == "unmapped_prefix" for v in vals if v.status == "invalid"))
        self.assertTrue(any(v.reason_code == "invalid_value_type" for v in vals if v.field == "OME_PIXEL_SIZE_X_UM"))


    def test_row_validation_4d_fields(self):
        vals = validate_row({
            "REMBI_EXPERIMENT_ID": "EXP-2",
            "REMBI_ACQUISITION_DATE": "2026-05-05",
            "OME_IMAGE_NAME": "img-2",
            "REMBI_BIOSAMPLE_TYPE": "NCIT:C123",
            "OME_PIXEL_SIZE_X_UM": 0.1,
            "OME_PIXEL_SIZE_Y_UM": 0.1,
            "OME_PIXEL_SIZE_Z_UM": 0.5,
            "OME_PIXEL_SIZE_T_S": 2.0,
            "OME_SIZE_X": 512,
            "OME_SIZE_Y": 512,
            "OME_SIZE_Z": 32,
            "OME_SIZE_T": 10,
        })
        invalid = [v for v in vals if v.status == "invalid"]
        self.assertEqual(invalid, [])

    def test_segmentation_mask_fields(self):
        vals = validate_row({
            "REMBI_EXPERIMENT_ID": "EXP-3",
            "REMBI_ACQUISITION_DATE": "2026-05-05",
            "OME_IMAGE_NAME": "img-mask",
            "REMBI_BIOSAMPLE_TYPE": "NCIT:C123",
            "MIFA_SEG_MASK_TYPE": "panoptic",
            "MIFA_SEG_MASK_URI": "s3://bucket/masks/img-mask-panoptic.ome.tiff",
            "MIFA_SEG_MASK_LABELSCHEME": "NCIT:C25218",
            "MIFA_SEG_MASK_CLASSES": 12,
        })
        invalid = [v for v in vals if v.status == "invalid"]
        self.assertEqual(invalid, [])

if __name__ == '__main__':
    unittest.main()
