# OMERO-Bifrost

<img align="left" width="100" height="100" src="https://github.com/qbicsoftware/omero-bifrost/blob/main/docs/images/bifrost_img.png?raw=true">

**OMERO-Bifrost** is a workflow-oriented abstraction layer for interoperable image and metadata operations across one or many [OMERO servers](https://omero.readthedocs.io/en/stable/). It exposes a stable Python package + CLI for deterministic **query / push / pull** operations in local, HPC, and cloud pipelines.

From a scientific data-management perspective, OMERO-Bifrost is designed to operationalize FAIR data stewardship in day-to-day pipeline execution: metadata stays machine-actionable, provenance remains auditable, and workflow inputs/outputs are deterministic. The FAIR layer aligns bioimaging reporting practices from **REMBI** and **MIFA** with practical **OME** mappings so automated pipelines can preserve biological context, technical acquisition parameters, and quality-control annotations while remaining interoperable across institutions.

In short, OMERO-Bifrost separates workflow logic from infrastructure details. Pipelines can keep a single operational contract (query/push/pull artifacts), while deployment-specific concerns (credentials, host, OMERO group scope) are supplied through server profiles.

---

## Requirements

- Python `3.10+`
- typer `0.24.1`
- rich `15.0.0`
- zeroc-ice `3.6.5`
- omero-py `5.22.1`
- omero-upload `0.4.0`
- ezomero `3.2.3`

## Installation

```bash
pip install omero-bifrost
```

If `zeroc-ice` source compilation fails, install the Glencoe binary wheel first (OMERO-recommended), then install dependencies:

```bash
python -m pip install "zeroc-ice @ https://github.com/glencoesoftware/zeroc-ice-py-linux-x86_64/releases/download/20240202/zeroc_ice-3.6.5-cp312-cp312-manylinux_2_28_x86_64.whl"
python -m pip install -r requirements.txt
```

Wheel catalog / platform guidance:
- https://www.glencoesoftware.com/blog/2023/12/08/ice-binaries-for-omero.html
- https://omero.readthedocs.io/en/stable/users/cli/installation.html

Container builds use the same approach via `ICE_WHEEL_URL` in `Dockerfile`.

## CLI overview

```bash
omero-bifrost --help
```

Command groups:
- `query`: inspect OMERO objects and metadata-filtered image IDs
- `push`: import image data and write annotations
- `pull`: export OME-TIFF, OME-XML metadata, and original files

---

## Configuration

Default config file: `./imaging_config.properties`.

Supported profile section format (required): `[OmeroServer:<profile>]`

```ini
[OmeroServer:eu]
omero.username = eu_user
omero.password = eu_password
omero.host = eu.omero.example.org
omero.port = 4064
omero.group = eu-imaging
```

Validation / resolution behavior:
- required keys per profile: `omero.username`, `omero.password`, `omero.host`, `omero.port`, `omero.group`
- `omero.port` must parse as integer
- unknown profile names and missing keys fail early with actionable errors
- `omero.group` is mandatory and resolved at connection time into `bifrost_group_context`
- unresolved/inaccessible group fails hard with `OmeroGroupResolutionError`

Example profile-oriented usage:

```bash
omero-bifrost --server-profile eu query img-ids --p-name StudyA --tag qc_pass --output eu_ids.json --to-file
omero-bifrost --server-profile us push img-file ./incoming/plate01_A01.ome.tiff 12345 --to-console
omero-bifrost --server-profile archive pull ome-tiffs ./exports --img-id 998877 --output ./exports/archive_pull.json --to-file
omero-bifrost --server-profile archive pull ome-xmls ./exports --img-id 998877
```

---

## FAIR metadata layer (REMBI + MIFA with OME alignment)

Core behavior:
- deterministic `key:value` filter parsing with equality semantics
- metadata tables require `IMAGE_DATA_PATH`; directory rows expand deterministically to sorted image targets
- ontology values support NCIT in code/CURIE/URI forms and normalize to canonical `NCIT:*`
- field-level validation returns reason-coded statuses for gating/auditing

Reason-code examples: `missing_required_field`, `invalid_value_type`, `unknown_term`, `malformed_id`, `unmapped_prefix`.

Required schema properties:
- `REMBI_EXPERIMENT_ID`
- `REMBI_ACQUISITION_DATE`
- `OME_IMAGE_NAME`
- `REMBI_BIOSAMPLE_TYPE`

Schema property set (typed validation + OME mapping):
- REMBI core: `REMBI_EXPERIMENT_ID`, `REMBI_ACQUISITION_DATE`, `REMBI_BIOSAMPLE_TYPE`, `REMBI_DISEASE`, `REMBI_ORGANISM_PART`
- OME image/instrument: `OME_IMAGE_NAME`, `OME_INSTRUMENT_ID`, `OME_OBJECTIVE_ID`
- OME calibration/dimensions: `OME_PIXEL_SIZE_X_UM`, `OME_PIXEL_SIZE_Y_UM`, `OME_PIXEL_SIZE_Z_UM`, `OME_PIXEL_SIZE_T_S`, `OME_SIZE_X`, `OME_SIZE_Y`, `OME_SIZE_Z`, `OME_SIZE_T`
- MIFA/QC/segmentation: `MIFA_QC_STATUS`, `MIFA_CALIBRATION_DATE`, `MIFA_OPERATOR_ID`, `MIFA_SEG_MASK_TYPE`, `MIFA_SEG_MASK_URI`, `MIFA_SEG_MASK_LABELSCHEME`, `MIFA_SEG_MASK_CLASSES`

Notes:
- unknown metadata keys are accepted as generic metadata
- schema-listed fields receive typed validation and OME alignment reporting

See details:
- `docs/fair-metadata.md`
- `src/omero_bifrost/fair/metadata_schema.py`

---

## Architecture (constellation model)

A **constellation** is a set of OMERO endpoints operated through one workflow-facing interface.

Design split:
- workflow concerns: deterministic commands, file artifacts, reproducible process chaining
- infrastructure concerns: endpoint host, credentials, and group scope

Operational boundary:
- **query**: discover/filter and emit IDs
- **push**: import images and metadata annotations
- **pull**: export OME-TIFF, export OME-XML, retrieve originals

Execution contract:
- OMERO subprocess calls are centralized in `run_omero_cli`
- commands are executed as argument lists (`shell=False`)
- `stdout`/`stderr` are captured as text for deterministic downstream handling
