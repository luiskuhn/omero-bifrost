# OMERO-Bifrost

<img align="left" width="100" height="100" src="https://github.com/qbicsoftware/omero-bifrost/blob/main/docs/images/bifrost_img.png?raw=true">

**OMERO-Bifrost** is a workflow-oriented abstraction layer for interoperable image and (meta)data operations across one or multiple [OMERO servers](https://omero.readthedocs.io/en/stable/). It provides a stable Python package and CLI interface for **query / push / pull** operations so the same automation logic can run reproducibly across local, HPC, and cloud environments.

From a scientific data-management perspective, OMERO-Bifrost is designed to operationalize established community practices around FAIR stewardship, bioimaging metadata reporting, and interoperable exchange formats. In practical terms, this means pipelines can preserve provenance-relevant metadata while using deterministic process inputs/outputs that are auditable and reproducible.

<br>

---

## Requirements

- Python `3.8`
- typer `0.9.0`
- rich `13.5.2`
- zeroc-ice `3.6.5`
- omero-py `5.13.1` (downgraded from `5.15.0` given ezomero `2.1.0` requirements)
- omero-upload `0.4.0`
- ezomero `2.1.0`

## Install with PyPI

`pip install omero-bifrost`

## Usage

Type `omero-bifrost --help` to see all commands and subcommands.

Current command groups:
- `query`: inspect OMERO objects and metadata-filtered image IDs
- `push`: import images and write annotations to OMERO
- `pull`: export OME-TIFFs and download original files

---

## Configuration

`omero-bifrost` reads credentials from a properties file (default: `./imaging_config.properties`).

### Single-server configuration

```ini
[OmeroServerSection]
omero.username = my_user
omero.password = my_password
omero.host = omero.example.org
omero.port = 4064
# Optional group context (group name or numeric id)
omero.group = my-lab-group
```

### Multi-server configuration (constellation deployments)

```ini
[OmeroServerSection.eu]
omero.username = eu_user
omero.password = eu_password
omero.host = eu.omero.example.org
omero.port = 4064
omero.group = eu-imaging

[OmeroServerSection.us]
omero.username = us_user
omero.password = us_password
omero.host = us.omero.example.org
omero.port = 4064
omero.group = us-screening

[OmeroServerSection.archive]
omero.username = archive_user
omero.password = archive_password
omero.host = archive.omero.example.org
omero.port = 4064
omero.group = archive-readonly
```

### Multi-server notes and recommended pattern

- `omero.group` is optional for backward compatibility.
- When provided, it is propagated to both BlitzGateway connections and CLI-backed commands.
- The built-in parser consumes `OmeroServerSection` directly.
- In multi-profile workflows, wrappers typically select one profile (`eu`, `us`, `archive`) and materialize it at runtime as `OmeroServerSection` for the specific command invocation.
- Keep credentials endpoint-specific and externalized from pipeline code.

### Profile-oriented usage examples

In pipeline wrappers (for example Nextflow module entrypoints), a `--server-profile` flag is commonly used to select `eu`, `us`, or `archive` before invoking `omero-bifrost`.

```bash
# Query on EU server profile
omero-bifrost --server-profile eu query img-ids \
  --p-name StudyA --tag qc_pass \
  --output eu_ids.tsv --to-file

# Push to US server profile
omero-bifrost --server-profile us push img-file \
  ./incoming/plate01_A01.ome.tiff 12345 --to-xml

# Pull from ARCHIVE server profile
omero-bifrost --server-profile archive pull ome-tiff \
  998877 --output ./exports/archive_img_998877.ome.tiff
```

If you run the CLI directly without a wrapper, use `--config` with a concrete single active section file per invocation.

---

## Tool architecture and constellation model

### Purpose

OMERO-Bifrost provides a stable automation layer over one or more OMERO servers, enabling pipelines to execute the same read/write data operations independent of where the underlying server is hosted.

In this context, a **constellation** means multiple OMERO endpoints coordinated through one workflow-facing command interface.

### Core design principle

The tool separates:

- **Workflow concerns**: deterministic commands, file-based artifacts, process chaining.
- **Infrastructure concerns**: server host, credentials, group context, and endpoint-specific access.

This separation allows Nextflow/nf-core modules to remain portable while endpoint details are supplied by configuration.

### Abstraction boundary

OMERO-Bifrost intentionally exposes a compact set of operational capabilities:

- **query**: discover/filter objects and emit image identifiers.
- **push**: import image data and write metadata/annotations.
- **pull**: export OME-TIFF and/or retrieve original files.

These operations are intended to be composable building blocks for workflows rather than a full replacement for interactive OMERO clients.

### Reproducibility implications

By favoring explicit inputs and outputs per command, pipelines can:

- materialize intermediate state as artifacts (e.g., TSV of image IDs),
- rerun individual process steps deterministically,
- improve auditability and provenance tracking.

### OMERO CLI execution and error contract

Subprocess-backed OMERO operations are centralized in `omero_cli_runner.run_omero_cli`, which always executes argument lists (`shell=False`) and captures `stdout`/`stderr` as text for deterministic downstream handling.

Contract details:

- Successful calls return a typed `CommandResult` with `returncode`, `stdout`, `stderr`, `cmd`, and optional `artifacts`.
- Non-zero OMERO CLI exits raise `OmeroCliCommandError` and include the captured `CommandResult`.
- Missing or malformed expected records in stdout (e.g., `Image:`, `OriginalFile:`, `TagAnnotation:`, `FileAnnotation:`, `ImageAnnotationLink:`) raise `OmeroCliParseError`.
- CLI handlers map these controlled exceptions to deterministic terminal output using `ERROR|<ExceptionType>|<message>` and exit with non-zero status.

This behavior is intended for workflow engines (Nextflow/nf-core) so failures are explicit, parseable, and never represented as ambiguous empty strings/lists.

---

## Nextflow / nf-core integration guide

### Why this integration model

OMERO-Bifrost is designed for process-level orchestration: each command performs one focused operation and emits artifacts that can be consumed by downstream workflow steps.

This aligns naturally with Nextflow and nf-core design principles around modularity, portability, and reproducibility.

### Configuration strategy for workflow engines

Store endpoint-specific details in configuration files and keep workflow logic generic.

Recommended practices:

- mount config files at runtime rather than hard-coding credentials,
- use secret managers or secured runtime environments for sensitive values,
- avoid embedding server-specific assumptions in process scripts,
- if using profile wrappers, select one profile (for example `--server-profile eu`) and materialize it as `OmeroServerSection` for the invoked command.

### Process composition pattern

A common high-level pattern is:

1. **query** selected records from OMERO and emit `ids.tsv`.
2. **push** data/annotations linked to selected IDs.
3. **pull** OME-TIFF/original files for analysis or archival workflows.

Because each step reads/writes explicit files, workflows can resume from intermediates and preserve provenance more easily.

### Module-oriented guidance (nf-core style)

When wrapping OMERO-Bifrost commands in reusable modules:

- keep command signatures narrow and explicit,
- expose paths for all produced artifacts,
- ensure process behavior is independent of local filesystem assumptions,
- document expected schema for intermediate files (e.g., TSV columns).

### Portability checklist

- [ ] No credentials hard-coded in pipeline source.
- [ ] OMERO endpoint fully provided at runtime.
- [ ] Intermediate artifacts persisted as files.
- [ ] Command invocations deterministic for the same inputs.

### End-to-end ETL example (REMBI/MIFA-aligned metadata, Nextflow abstraction layer)

Instead of adding a monolithic CLI ETL command, implement ETL at the workflow layer by composing existing `query`, `push`, and `pull` operations.

#### Metadata input table (TSV)

Use one row per image file (comparable to OMERO metadata registration sheets used in ETL pipelines):

- `filename` (required): must match the basename of the image file to import.
- `dataset_id` (optional): OMERO dataset ID. If omitted, use a workflow/global `params.dataset_id`.
- `kv_pairs` (optional): semicolon-separated `key:value` entries (must use `:` because `omero-bifrost push key-value --kv-pair` expects `key:value`).
- `tags` (optional): semicolon-separated OMERO tags.

Example:

```tsv
filename	dataset_id	kv_pairs	tags
img_001.ome.tiff	12345	SpecimenID:SP-001;REMBI.BiologicalEntity:cell_culture;MIFA.ImagingModality:confocal	REMBI_minimal;MIFA_qc_pass
img_002.ome.tiff	12345	SpecimenID:SP-002;REMBI.BiologicalEntity:tissue;MIFA.ImagingModality:widefield	REMBI_minimal;MIFA_qc_review
```

### Nextflow example for folder import + annotation (nf-core style)

The example below follows nf-core conventions:
- DSL2
- `tuple val(meta), path(...)` channel contracts
- one tool responsibility per process
- explicit container per process (fictional personal DockerHub image)
- `versions.yml` output for provenance

```nextflow
nextflow.enable.dsl = 2

params.input_dir      = "${baseDir}/incoming_images"
params.metadata_tsv   = "${baseDir}/metadata/rembi_mifa.tsv"
params.dataset_id     = "12345"
params.config_file    = "${baseDir}/imaging_config.properties"
params.server_profile = "OmeroServerSection"
params.container      = "docker.io/mydockerhubuser/omero-bifrost:latest"

process OMERO_BIFROST_IMPORT {
    tag "${meta.id}"
    container "${params.container}"

    input:
    tuple val(meta), path(image_file), path(metadata_tsv)

    output:
    tuple val(meta), path("imported_image.tsv"), emit: imported
    path "versions.yml", emit: versions

    script:
    """
    DATASET_ID=\$(awk -F '\\t' -v fn="\$(basename ${image_file})" '
      NR==1{
        for(i=1;i<=NF;i++){ if(\$i=="filename") f=i; if(\$i=="dataset_id") d=i }
      }
      NR>1 && \$f==fn { if (d>0 && length(\$d)>0) print \$d; exit }' ${metadata_tsv})
    DATASET_ID=\${DATASET_ID:-${params.dataset_id}}

    omero-bifrost push img-file \\
      ${image_file} \\
      \${DATASET_ID} \\
      --config ${params.config_file} \\
      --server-profile ${params.server_profile} \\
      --to-xml > import.xml

    python ${projectDir}/bin/extract_imported_image_id.py import.xml ${image_file} imported_image.tsv
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
      python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}

process OMERO_BIFROST_ANNOTATE {
    tag "${meta.id}"
    container "${params.container}"

    input:
    tuple val(meta), path(imported_tsv), path(metadata_tsv)

    output:
    tuple val(meta), path("annotation_done.tsv"), emit: annotated
    path "versions.yml", emit: versions

    script:
    """
    python ${projectDir}/bin/annotate_imported_image.py \\
      ${imported_tsv} ${metadata_tsv} \\
      ${params.config_file} ${params.server_profile} annotation_done.tsv
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
      python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}

process OMERO_BIFROST_QUERY_QC {
    tag "${meta.id}"
    container "${params.container}"

    input:
    tuple val(meta), path(annotation_tsv)

    output:
    tuple val(meta), path("qc_query.tsv"), emit: qc
    path "versions.yml", emit: versions

    script:
    """
    omero-bifrost query img-ids \\
      --tag REMBI_minimal \\
      --output qc_query.tsv \\
      --config ${params.config_file} \\
      --server-profile ${params.server_profile}
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
      omero_bifrost: "cli"
    END_VERSIONS
    """
}

workflow {
    Channel
        .fromPath("${params.input_dir}/*", type: 'file')
        .map { file -> tuple([id: file.baseName], file, file(params.metadata_tsv)) }
        .set { ch_images_meta }

    ch_imported = OMERO_BIFROST_IMPORT(ch_images_meta).imported
    ch_metadata = Channel.value(file(params.metadata_tsv))
    ch_imported_with_meta = ch_imported
        .combine(ch_metadata)
        .map { rec, metadata -> tuple(rec[0], rec[1], metadata) }

    ch_annotated = OMERO_BIFROST_ANNOTATE(ch_imported_with_meta).annotated
    OMERO_BIFROST_QUERY_QC(ch_annotated)
}
```

This abstraction-layer pattern mirrors the intent of OMERO registration scripts (upload → receive ID → enrich with metadata), while preserving reproducibility through explicit per-step artifacts and containerized runtime.
For a full nf-core pipeline, prefer moving helper scripts into tested module wrappers under `modules/local/`.

---

## FAIR metadata and standards mapping

### Scope

This section summarizes how OMERO-Bifrost supports FAIR-oriented metadata handling in workflow automation contexts.

### Standards and formats in scope

#### REMBI

REMBI provides recommendations for minimum information reporting in bioimaging. In OMERO-Bifrost workflows, REMBI-aligned fields should be captured and propagated as structured metadata where possible.

#### MIFA

MIFA offers guidance for microscopy experiment annotation and quality-related metadata. OMERO-Bifrost metadata operations should preserve these annotations to improve interpretability and reuse.

#### OME data model

The OME model acts as a canonical semantic framework for microscopy metadata. OMERO-Bifrost operations should maintain consistency with OME entities/relationships during query, ingestion, annotation, and export workflows.

#### Bio-Formats

Bio-Formats interoperability supports broad microscopy format compatibility. OMERO-Bifrost workflows should prefer ingestion/export paths that remain compatible with Bio-Formats-enabled tooling in downstream analysis ecosystems.

#### OME-TIFF

OME-TIFF provides a portable, metadata-aware exchange format for microscopy data. In OMERO-Bifrost, OME-TIFF export serves reproducible transport between acquisition, management, and analysis stages.

### Practical FAIR implementation notes

To improve findability, accessibility, interoperability, and reusability in pipelines:

- preserve provenance-relevant metadata during push/pull operations,
- keep machine-readable intermediate artifacts for selection and transformation steps,
- standardize metadata field naming in workflow outputs,
- document assumptions and transformations in pipeline/module docs.

### Implementation principle

OMERO-Bifrost does not replace domain standards; it operationalizes them by providing stable workflow-facing commands that can be embedded in reproducible process graphs.

---

## Scientific grounding and references

OMERO-Bifrost is positioned as an implementation-oriented bridge between scientific data standards and workflow engineering:

- FAIR principles define the high-level data stewardship goals for findability, accessibility, interoperability, and reuse [1].
- REMBI and MIFA provide microscopy-focused reporting and annotation guidance that can be captured and propagated through OMERO workflows [2,3].
- The OME data model and OMERO platform provide the conceptual and operational backbone for microscopy metadata/data management [4,5].
- Bio-Formats and OME-TIFF support broad format interoperability and transport across analysis ecosystems [6,7].
- Workflow reproducibility patterns are aligned with process-oriented workflow systems such as Nextflow and nf-core [8,9].

### Reference list

1. Wilkinson MD, Dumontier M, Aalbersberg IJ, et al. The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*. 2016;3:160018. doi:[10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18)
2. Sarkans U, Chiu W, Collinson L, et al. REMBI: Recommended Metadata for Biological Images—enabling reuse of microscopy data in biology. *Nature Methods*. 2021;18:1418–1422. doi:[10.1038/s41592-021-01166-8](https://doi.org/10.1038/s41592-021-01166-8)
3. Sarkans U, Hammer M, Lloret-Llinares M, et al. MIFA: A FAIR microscopy metadata schema for automated and reproducible workflows. *Nature Methods*. 2025. doi:[10.1038/s41592-025-02663-5](https://doi.org/10.1038/s41592-025-02663-5)
4. Goldberg IG, Allan C, Burel J-M, et al. The Open Microscopy Environment (OME) Data Model and XML File: Open tools for informatics and quantitative analysis in biological imaging. *Genome Biology*. 2005;6:R47. doi:[10.1186/gb-2005-6-5-r47](https://doi.org/10.1186/gb-2005-6-5-r47)
5. Allan C, Burel J-M, Moore J, et al. OMERO: flexible, model-driven data management for experimental biology. *Nature Methods*. 2012;9:245–253. doi:[10.1038/nmeth.1896](https://doi.org/10.1038/nmeth.1896)
6. Linkert M, Rueden CT, Allan C, et al. Metadata matters: access to image data in the real world. *Journal of Cell Biology*. 2010;189(5):777–782. doi:[10.1083/jcb.201004104](https://doi.org/10.1083/jcb.201004104)
7. OME Consortium. OME-TIFF specification. https://docs.openmicroscopy.org/ome-model/latest/ome-tiff/
8. Di Tommaso P, Chatzou M, Floden EW, et al. Nextflow enables reproducible computational workflows. *Nature Biotechnology*. 2017;35:316–319. doi:[10.1038/nbt.3820](https://doi.org/10.1038/nbt.3820)
9. Ewels PA, Peltzer A, Fillinger S, et al. The nf-core framework for community-curated bioinformatics pipelines. *Nature Biotechnology*. 2020;38:276–278. doi:[10.1038/s41587-020-0439-x](https://doi.org/10.1038/s41587-020-0439-x)

---

## Tooling and API documentation

- **omero-py** (Python bindings): https://omero.readthedocs.io/en/stable/developers/Python.html
- **OMERO CLI documentation**: https://omero.readthedocs.io/en/stable/users/cli/index.html
- **OMERO API documentation (developer index)**: https://omero.readthedocs.io/en/stable/developers/
- **ezomero** (high-level OMERO Python helpers): https://thejacksonlaboratory.github.io/ezomero/
- **Bio-Formats developer/user docs**: https://bio-formats.readthedocs.io/

---

## Development notes

To install packages in `requirements.txt` in the current conda env:

`pip install -r requirements.txt`

To test package, install using pip:

`pip install -e .`
