# OMERO-Bifrost

<img align="left" width="100" height="100" src="https://github.com/qbicsoftware/omero-bifrost/blob/main/docs/images/bifrost_img.png?raw=true">

**OMERO-Bifrost** is a workflow-oriented abstraction layer for interoperable image and metadata operations across one or many [OMERO servers](https://omero.readthedocs.io/en/stable/). It is built for organizations that need to manage, process, and analyze bioimage data at scale, where repositories are large, distributed, and continuously updated.

The tool exposes a standardized OMERO remote-operation surface through a stable Python package + CLI, centered on deterministic **query / push / pull** primitives. This gives Nextflow/nf-core pipelines a consistent command contract independent of deployment topology (single-site, multi-site, HPC, or cloud), while preserving machine-readable outputs and workflow-safe, parseable error behavior.

Its **constellation model** treats multiple OMERO endpoints as one FAIR-federated operational space: workflow logic stays uniform, and endpoint-specific concerns (host, credentials, group scope, access policy) are injected through server profiles. This separation is key for scaling digital repository/workflow infrastructure without rewriting pipeline modules per institution or per environment.

From a metadata perspective, OMERO-Bifrost operationalizes FAIR stewardship with a constrained, validation-first layer aligned to **REMBI** and **MIFA**, with pragmatic **OME** mappings and ontology normalization (currently NCIT). The result is reproducible metadata ingestion, auditable provenance, and standards-aware interoperability for both single OMERO deployments and distributed federated OMERO collections.

---

## Documentation

The documentation set is organized for teams building large-scale OMERO-based digital infrastructure: start from federation/abstraction design, continue with FAIR metadata semantics, then implement workflow orchestration patterns for production pipelines.

### Architecture
Explains how OMERO-Bifrost supports scaling from a single OMERO server to a FAIR-federated constellation of repositories through one standardized operational API. It details the abstraction boundary (query/push/pull), profile-based endpoint resolution, deterministic execution records, and failure categorization needed for robust cross-site automation. It also covers production hardening controls (timeout/retry/fail policy) and provenance envelopes for federated operations.

- [Architecture: OMERO-Bifrost as an abstraction layer](docs/architecture.md)

### FAIR metadata and standards mapping
Describes the FAIR metadata layer required to keep large OMERO repositories interoperable across institutions and workflows. It documents REMBI/MIFA intent, explicit OME-aligned mappings, ontology normalization rules (including NCIT code/CURIE/URI forms), and reason-coded validation outcomes for QC gating and audit trails. It also defines deterministic ingestion semantics so metadata handling remains reproducible in both local and federated contexts.

- [FAIR metadata and standards mapping](docs/fair-metadata.md)

### Nextflow / nf-core integration
Covers how Nextflow/nf-core pipelines can consume OMERO-Bifrost as a standardized CLI control plane for repository-scale workflows. It includes runtime configuration and secret-handling strategies, module-oriented process design, artifact-driven chaining across query/push/pull stages, and a worked ETL pattern for import, annotation enrichment, and QC selection. The guide emphasizes portability and reproducibility for both single-server and federated multi-server deployments.

- [Nextflow / nf-core integration guide](docs/nextflow-nfcore.md)

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

## CLI command reference (detailed, compressed)

Interface shape: `omero-bifrost <group> <command> [args/options]` with groups `query`, `push`, `pull`.

### Common options and execution semantics

For commands that expose them, shared options are:
- `--config/-c <path:str>` (default `./imaging_config.properties`)
- `--server-profile/-s <profile:str>` (default `default`)
- `--output/-o <path:str>` (default `./omero_bifrost_output.json`)
- `--to-file` (write JSON envelope to `--output`)
- `--to-console` (interface-consistency flag; envelope prints to stdout whenever `--to-file` is false)

Parameter model (Typer-backed):
- Positional arguments are required unless syntax marks otherwise.
- Repeatable list options use repeated flags (e.g., `--img-id 1 --img-id 2`).
- IDs are often accepted as CLI strings and cast downstream; invalid coercions raise `ValueError` (deterministic `ERROR|...` non-zero exit).
- `--kv-pair` uses strict `key:value` parsing via `parse_filter_exprs`; malformed tokens raise `FilterParseError`.

Config/profile resolution per invocation:
- `--config` + `--server-profile` resolve `[OmeroServer:<profile>]`.
- Required keys: `omero.username`, `omero.password`, `omero.host`, `omero.port`, `omero.group`.

Special-case divergence:
- `pull ome-xmls` prints output paths line-by-line and does not currently expose `--output/--to-file/--to-console`.

### Command matrix (all commands, full parameter contracts)

| Group | Command | Positional args | Command-specific options | Shared options available | Output behavior |
|---|---|---|---|---|---|
| query | `list-all` | none | none | all shared | JSON envelope (`records` from accessible objects) |
| query | `dataset-id` | `<project:str> <dataset:str>` | none | all shared | JSON envelope with resolved dataset ID |
| query | `img-ids` | none | `--p-name <name:str>` repeatable; `--kv-pair <key:value>` repeatable (AND narrowing); `--tag <value:str>` repeatable (AND narrowing) | all shared | JSON envelope with filtered image IDs + path/name |
| push | `img-file` | `<file_path:str> <dataset_id:str>` (cast to `int`) | none | all shared | JSON envelope with imported image IDs |
| push | `img-folder` | `<folder_path:str> <dataset_id:str>` (cast to `int`, depth=1 intent) | none | all shared | JSON envelope with imported image IDs |
| push | `key-value` | `<image_id:str>` | `--kv-pair <key:value>` repeatable (required); `--validation-policy <strict\|lenient>` default `strict` | all shared | JSON envelope with metadata update count; strict aborts on first invalid field, lenient skips invalid + warns |
| push | `img-tag` | `<image_id:str> <tag_value:str>` | `--desc/-d <text:str>` default empty; used if tag creation needed | all shared | JSON envelope with link op stdout/stderr |
| push | `file-atch` | `<file_path:str> <image_id:str>` | none | all shared | JSON envelope with created file-annotation ID |
| pull | `ome-tiffs` | `<output_path:str>` | `--img-id <id:str>` repeatable; `--list/-l <tsv_path:str>` overrides `--img-id` if non-empty | all shared | JSON envelope; files named `omero_img_id_<ID>__<NAME>.ome.tiff` |
| pull | `ome-xmls` | `<output_path:str>` | `--img-id <id:str>` repeatable; `--list/-l <tsv_path:str>` overrides `--img-id` if non-empty | `--config/-c`, `--server-profile/-s` only | prints `.ome.xml` paths line-by-line |
| pull | `orig-files` | `<output_path:str>` | `--img-id <id:str>` repeatable; `--list/-l <tsv_path:str>` overrides `--img-id` if non-empty | all shared | JSON envelope; files named `omero_file_id_<FILE_ID>__<ORIGINAL_FILENAME>` |

### Constellation interface semantics (single vs multi-server)

Current behavior:
- CLI invocation targets one profile via `--server-profile`.
- Multi-server orchestration is programmatic (`src/omero_bifrost/federation`), not a first-class CLI fan-out flag.

Federation APIs:
- `federated_query(profiles, query_fn, fail_policy='continue')`
- `federated_push(profiles, push_fn, fail_policy='continue')`
- `federated_annotate(profiles, annotate_fn, fail_policy='continue')`
- `federated_pull(targets, pull_fn, fail_policy='continue')` where each `PullTarget` explicitly carries `server_profile`, `target_id`, `target_type`.

Execution guarantees (FederationRunner):
- Profiles are deduplicated/sorted; work runs via thread pool.
- Failure policy: `continue` (default) or `fail-fast`.
- Resilience knobs: `timeout_seconds`, `retries`, exponential `backoff_seconds`.
- Output shape: `{provenance, profiles, records}` with normalized record schema and categorized failures (`auth`, `group_scope`, `validation`, `transient_network`, `unexpected`).

Semantic invariants for robust constellation design:
- Canonical federated identity should be `(server_profile, local_object_id)`.
- Keep query outputs profile-qualified before downstream push/pull.
- Use explicit `PullTarget` contracts whenever host ambiguity is possible.
- For uniform automation, consider aligning `pull ome-xmls` to JSON-envelope conventions.

### Fictional examples (single server + constellation)

> All examples are fictional placeholders.

- `query list-all`
  - single: `omero-bifrost query list-all --server-profile eu-hospital --to-file --output ./out/eu_list_all.json`
  - constellation: `federated_query(["eu-hospital","us-core","apac-node"], query_fn=list_all_for_profile)`
- `query dataset-id`
  - single: `omero-bifrost query dataset-id CancerAtlas CohortA --server-profile us-core --to-console`
  - constellation: `federated_query(["eu-hospital","us-core"], query_fn=lambda p: dataset_id_for_profile(p, "CancerAtlas", "CohortA"))`
- `query img-ids`
  - single: `omero-bifrost query img-ids --server-profile eu-hospital --p-name LiverStudy --kv-pair REMBI_EXPERIMENT_ID:EXP-2042-0007 --tag qc_pass --to-file --output ./out/eu_img_ids.json`
  - constellation: `federated_query(profiles, query_fn=lambda p: img_ids_for_profile(p, projects=["LiverStudy"], kv_pairs=["REMBI_EXPERIMENT_ID:EXP-2042-0007"], tags=["qc_pass"]))`
- `push img-file`
  - single: `omero-bifrost push img-file ./incoming/slide_A01.ome.tiff 120045 --server-profile us-core --to-file --output ./out/push_img_file.json`
  - constellation: `federated_push(profiles, push_fn=lambda p: push_file_for_profile(p, "./incoming/slide_A01.ome.tiff", dataset_map[p]))`
- `push img-folder`
  - single: `omero-bifrost push img-folder ./incoming/batch_17 99110 --server-profile apac-node --to-console`
  - constellation: `federated_push(profiles, push_fn=lambda p: push_folder_for_profile(p, "./incoming/batch_17", dataset_map[p]))`
- `push key-value`
  - single: `omero-bifrost push key-value 998877 --server-profile eu-hospital --kv-pair REMBI_EXPERIMENT_ID:EXP-2042-0007 --kv-pair MIFA_QC_STATUS:PASS --validation-policy lenient --to-file --output ./out/push_kv.json`
  - constellation: `federated_annotate(profiles, annotate_fn=lambda p: annotate_kv_for_profile(p, image_id=image_map[p], kv_pairs=[...], policy="lenient"))`
- `push img-tag`
  - single: `omero-bifrost push img-tag 998877 qc_reviewed --server-profile eu-hospital --desc "Curator-reviewed" --to-console`
  - constellation: `federated_annotate(profiles, annotate_fn=lambda p: add_tag_for_profile(p, image_map[p], "qc_reviewed", "Curator-reviewed"))`
- `push file-atch`
  - single: `omero-bifrost push file-atch ./reports/qc_A01.pdf 998877 --server-profile eu-hospital --to-file --output ./out/push_attach.json`
  - constellation: `federated_push(profiles, push_fn=lambda p: attach_file_for_profile(p, "./reports/qc_A01.pdf", image_map[p]))`
- `pull ome-tiffs`
  - single: `omero-bifrost pull ome-tiffs ./exports/eu --server-profile eu-hospital --img-id 998877 --img-id 998878 --to-file --output ./out/pull_tiffs.json`
  - constellation: `federated_pull([PullTarget("eu-hospital","998877","Image"), PullTarget("us-core","445566","Image")], pull_fn=pull_tiff_for_target)`
- `pull ome-xmls`
  - single: `omero-bifrost pull ome-xmls ./exports/eu_xml --server-profile eu-hospital --img-id 998877`
  - constellation: `federated_pull([PullTarget("eu-hospital","998877","Image"), PullTarget("archive-west","778899","Image")], pull_fn=pull_xml_for_target)`
- `pull orig-files`
  - single: `omero-bifrost pull orig-files ./exports/originals --server-profile us-core --img-id 445566 --to-file --output ./out/pull_orig.json`
  - constellation: `federated_pull([PullTarget("eu-hospital","998877","Image"), PullTarget("us-core","445566","Image")], pull_fn=pull_original_for_target, fail_policy="fail-fast")`

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
