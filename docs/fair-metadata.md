# FAIR metadata and standards mapping

## Scope

This document defines the FAIR metadata layer used by OMERO-Bifrost for query/push workflows.
It focuses on deterministic parsing, ontology normalization, and validation records that can be consumed by workflow engines.

## REMBI + MIFA profile with OME leverage

The active metadata profile is intentionally constrained to fields that are:
1. useful for REMBI/MIFA reporting,
2. representable in OMERO annotations,
3. alignable to OME model concepts.

### Profile fields and OME mapping

| Field | Standard intent | OME concept |
|---|---|---|
| `REMBI_EXPERIMENT_ID` | REMBI experiment identity | `ExperimenterGroup/Project` |
| `REMBI_ACQUISITION_DATE` | REMBI acquisition context | `Image/AcquisitionDate` |
| `OME_IMAGE_NAME` | OME native image naming | `Image/Name` |
| `OME_INSTRUMENT_ID` | OME native instrument identity | `Instrument/@ID` |
| `OME_OBJECTIVE_ID` | Optical objective identity | `Instrument/Objective/@ID` |
| `OME_PIXEL_SIZE_X_UM` | Spatial calibration | `Pixels/PhysicalSizeX` |
| `OME_PIXEL_SIZE_Y_UM` | Spatial calibration | `Pixels/PhysicalSizeY` |
| `OME_PIXEL_SIZE_Z_UM` | Axial calibration | `Pixels/PhysicalSizeZ` |
| `OME_PIXEL_SIZE_T_S` | Temporal calibration | `Pixels/TimeIncrement` |
| `OME_SIZE_X` | Image extent | `Pixels/SizeX` |
| `OME_SIZE_Y` | Image extent | `Pixels/SizeY` |
| `OME_SIZE_Z` | Image extent | `Pixels/SizeZ` |
| `OME_SIZE_T` | Time extent | `Pixels/SizeT` |
| `REMBI_BIOSAMPLE_TYPE` | Sample semantics | `Image/AnnotationRef` |
| `REMBI_DISEASE` | Biological semantics | `Image/AnnotationRef` |
| `REMBI_ORGANISM_PART` | Biological semantics | `Image/AnnotationRef` |
| `MIFA_QC_STATUS` | MIFA quality status | `Image/AnnotationRef` |
| `MIFA_CALIBRATION_DATE` | Instrument quality history | `Instrument/AnnotationRef` |
| `MIFA_OPERATOR_ID` | Experimenter identity | `Experimenter/@ID` |
| `MIFA_SEG_MASK_TYPE` | Segmentation mask flavor (`semantic`/`panoptic`) | `Image/AnnotationRef` |
| `MIFA_SEG_MASK_URI` | URI/path to mask artifact (for supervised training) | `Image/ROIRef` |
| `MIFA_SEG_MASK_LABELSCHEME` | Ontology-backed label scheme identifier | `Image/AnnotationRef` |
| `MIFA_SEG_MASK_CLASSES` | Number of supervised classes in mask | `Image/AnnotationRef` |

## Validation semantics

Validation emits per-field statuses with reason codes:
- `unknown_term`
- `malformed_id`
- `unmapped_prefix`
- `invalid_value_type`
- `missing_required_field`

Ontology-bearing fields accept NCIT identifiers as:
- code (e.g., `C1234`)
- CURIE (e.g., `NCIT:C1234`)
- URI (e.g., `http://purl.obolibrary.org/obo/NCIT_C1234`)

All normalize to canonical CURIE output (`NCIT:C1234`) when valid.

## Deterministic ingestion contract

Metadata tables must include `IMAGE_DATA_PATH`.
Optional control columns are `SAMPLE_ID`, `OMERO_TAGS`, and `ETL_TAG`.
All other columns are treated as metadata keys.

Row expansion:
- file path row → one target image
- folder path row → sorted image targets

Error reporting is row-indexed for unresolved paths and conflicting metadata mappings.

## References

- FAIR principles: https://doi.org/10.1038/sdata.2016.18
- REMBI: https://doi.org/10.1038/s41592-021-01166-8
- MIFA: https://www.nature.com/articles/s41592-025-02663-5
- OME data model: https://doi.org/10.1186/gb-2005-6-5-r47
- OMERO platform: https://doi.org/10.1038/nmeth.1896


## Ontologies currently used

- **NCIT (NCI Thesaurus)** via prefix `NCIT` and base URI `http://purl.obolibrary.org/obo/NCIT_`.

At present, NCIT is the only ontology prefix configured in code for normalization/validation (including optional segmentation mask label schemes).
