"""Typed FAIR metadata schema and row validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ontology_normalization import normalize_term

# REMBI/MIFA-inspired profile with explicit OME alignment.
# Keys use OMERO map-annotation-safe names and point to OME concepts.
FIELD_SPEC = {
    # Required experiment identifiers
    "REMBI_EXPERIMENT_ID": {"required": True, "type": "string", "ome": "ExperimenterGroup/Project"},
    "REMBI_ACQUISITION_DATE": {"required": True, "type": "string", "ome": "Image/AcquisitionDate"},
    # OME-intrinsic fields frequently surfaced in OMERO
    "OME_IMAGE_NAME": {"required": True, "type": "string", "ome": "Image/Name"},
    "OME_INSTRUMENT_ID": {"required": False, "type": "string", "ome": "Instrument/@ID"},
    "OME_OBJECTIVE_ID": {"required": False, "type": "string", "ome": "Instrument/Objective/@ID"},
    "OME_PIXEL_SIZE_X_UM": {"required": False, "type": "number", "ome": "Pixels/PhysicalSizeX"},
    "OME_PIXEL_SIZE_Y_UM": {"required": False, "type": "number", "ome": "Pixels/PhysicalSizeY"},
    "OME_PIXEL_SIZE_Z_UM": {"required": False, "type": "number", "ome": "Pixels/PhysicalSizeZ"},
    "OME_PIXEL_SIZE_T_S": {"required": False, "type": "number", "ome": "Pixels/TimeIncrement"},
    "OME_SIZE_X": {"required": False, "type": "integer", "ome": "Pixels/SizeX"},
    "OME_SIZE_Y": {"required": False, "type": "integer", "ome": "Pixels/SizeY"},
    "OME_SIZE_Z": {"required": False, "type": "integer", "ome": "Pixels/SizeZ"},
    "OME_SIZE_T": {"required": False, "type": "integer", "ome": "Pixels/SizeT"},
    # Semantics-heavy fields using ontology normalization
    "REMBI_BIOSAMPLE_TYPE": {"required": True, "type": "ontology", "ome": "Image/AnnotationRef"},
    "REMBI_DISEASE": {"required": False, "type": "ontology", "ome": "Image/AnnotationRef"},
    "REMBI_ORGANISM_PART": {"required": False, "type": "ontology", "ome": "Image/AnnotationRef"},
    # MIFA quality metadata
    "MIFA_QC_STATUS": {"required": False, "type": "string", "ome": "Image/AnnotationRef"},
    "MIFA_CALIBRATION_DATE": {"required": False, "type": "string", "ome": "Instrument/AnnotationRef"},
    "MIFA_OPERATOR_ID": {"required": False, "type": "string", "ome": "Experimenter/@ID"},
    "MIFA_SEG_MASK_TYPE": {"required": False, "type": "string", "ome": "Image/AnnotationRef"},
    "MIFA_SEG_MASK_URI": {"required": False, "type": "string", "ome": "Image/ROIRef"},
    "MIFA_SEG_MASK_LABELSCHEME": {"required": False, "type": "ontology", "ome": "Image/AnnotationRef"},
    "MIFA_SEG_MASK_CLASSES": {"required": False, "type": "integer", "ome": "Image/AnnotationRef"},
}


@dataclass(frozen=True)
class FieldValidation:
    field: str
    status: str
    reason_code: str | None = None
    normalized_value: Any = None
    ome_path: str | None = None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_row(row: dict[str, Any]) -> list[FieldValidation]:
    out: list[FieldValidation] = []

    for field, spec in FIELD_SPEC.items():
        if spec.get("required") and (field not in row or row.get(field) in (None, "")):
            out.append(FieldValidation(field=field, status="invalid", reason_code="missing_required_field", ome_path=spec.get("ome")))

    for key, value in row.items():
        spec = FIELD_SPEC.get(key)
        if spec is None:
            out.append(FieldValidation(field=key, status="valid", normalized_value=value, ome_path=None))
            continue

        ftype = spec["type"]
        if value in (None, ""):
            out.append(FieldValidation(field=key, status="valid", normalized_value=value, ome_path=spec.get("ome")))
            continue

        if ftype == "ontology":
            norm, err = normalize_term(str(value))
            if err:
                out.append(FieldValidation(field=key, status="invalid", reason_code=err, ome_path=spec.get("ome")))
            else:
                out.append(FieldValidation(field=key, status="valid", normalized_value=norm, ome_path=spec.get("ome")))
        elif ftype == "number":
            if _is_number(value):
                out.append(FieldValidation(field=key, status="valid", normalized_value=float(value), ome_path=spec.get("ome")))
            else:
                out.append(FieldValidation(field=key, status="invalid", reason_code="invalid_value_type", ome_path=spec.get("ome")))
        elif ftype == "integer":
            if _is_integer(value):
                out.append(FieldValidation(field=key, status="valid", normalized_value=int(value), ome_path=spec.get("ome")))
            else:
                out.append(FieldValidation(field=key, status="invalid", reason_code="invalid_value_type", ome_path=spec.get("ome")))
        else:
            if isinstance(value, str):
                out.append(FieldValidation(field=key, status="valid", normalized_value=value.strip(), ome_path=spec.get("ome")))
            else:
                out.append(FieldValidation(field=key, status="invalid", reason_code="invalid_value_type", ome_path=spec.get("ome")))

    return out
