# Nextflow / nf-core integration guide

## Why this integration model

OMERO-Bifrost is designed for process-level orchestration: each command performs one focused operation and emits artifacts that can be consumed by downstream workflow steps.

This aligns naturally with Nextflow and nf-core design principles around modularity, portability, and reproducibility.

## Configuration strategy

Store endpoint-specific details in configuration files and keep workflow logic generic.

Typical single-server properties file:

```ini
[OmeroServerSection]
omero.username = my_user
omero.password = my_password
omero.host = omero.example.org
omero.port = 4064
omero.group = my-lab-group
```

Profile-oriented properties file pattern:

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

Recommended practices:

- mount config files at runtime rather than hard-coding credentials,
- use secret managers or secured runtime environments for sensitive values,
- avoid embedding server-specific assumptions in process scripts.
- if using profile wrappers, select one profile (for example `--server-profile eu`) and materialize it as `OmeroServerSection` for the invoked command.

## Process composition pattern

A common high-level pattern is:

1. **query** selected records from OMERO and emit `ids.tsv`.
2. **push** data/annotations linked to selected IDs.
3. **pull** OME-TIFF/original files for analysis or archival workflows.

Because each step reads/writes explicit files, workflows can resume from intermediates and preserve provenance more easily.

## Module-oriented guidance (nf-core style)

When wrapping OMERO-Bifrost commands in reusable modules:

- keep command signatures narrow and explicit,
- expose paths for all produced artifacts,
- ensure process behavior is independent of local filesystem assumptions,
- document expected schema for intermediate files (e.g., TSV columns).

## Portability checklist

- [ ] No credentials hard-coded in pipeline source.
- [ ] OMERO endpoint fully provided at runtime.
- [ ] Intermediate artifacts persisted as files.
- [ ] Command invocations deterministic for the same inputs.

## Example: Nextflow ETL for OMERO ingest + annotation

Use Nextflow as an abstraction layer above OMERO-Bifrost CLI commands, mirroring the upload→ID capture→metadata annotation logic used in registration scripts.

### Metadata TSV schema

Minimum recommended columns:
- `filename`: file name present in the input folder,
- `dataset_id` (optional): OMERO dataset ID; if not set, use pipeline default (`params.dataset_id`),
- `kv_pairs`: semicolon-separated `key:value` entries (must use `:` to match `omero-bifrost push key-value --kv-pair`),
- `tags`: semicolon-separated OMERO tag values.

Example:

```tsv
filename	dataset_id	kv_pairs	tags
img_001.ome.tiff	12345	SpecimenID:SP-001;REMBI.BiologicalEntity:cell_culture;MIFA.ImagingModality:confocal	REMBI_minimal;MIFA_qc_pass
img_002.ome.tiff	12345	SpecimenID:SP-002;REMBI.BiologicalEntity:tissue;MIFA.ImagingModality:widefield	REMBI_minimal;MIFA_qc_review
```

### Nextflow process (nf-core style, with DockerHub image)

Assume a working container image in a personal DockerHub account (fictional): `docker.io/mydockerhubuser/omero-bifrost:latest`.
The structure below follows nf-core patterns (`meta` maps, tuple I/O, process-local versions output, one responsibility per process).

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
        for(i=1;i<=NF;i++){
          if(\$i=="filename") f=i
          if(\$i=="dataset_id") d=i
        }
      }
      NR>1 && \$f==fn {
        if (d>0 && length(\$d)>0) print \$d;
        exit
      }' ${metadata_tsv})
    DATASET_ID=\${DATASET_ID:-${params.dataset_id}}

    omero-bifrost push img-file \
      ${image_file} \
      \${DATASET_ID} \
      --config ${params.config_file} \
      --server-profile ${params.server_profile} \
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
    python ${projectDir}/bin/annotate_imported_image.py \
      ${imported_tsv} ${metadata_tsv} \
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
    omero-bifrost query img-ids \
      --tag REMBI_minimal \
      --output qc_query.tsv \
      --config ${params.config_file} \
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

In a full nf-core pipeline, the two helper scripts referenced above (`bin/extract_imported_image_id.py`, `bin/annotate_imported_image.py`) should be modularized under `modules/local/` wrappers and covered by module tests.

### REMBI/MIFA guidance notes

- Use stable ontology-backed field names in `kv_pairs` (for example `REMBI.*` / `MIFA.*` keys) to improve interoperability.
- Version the TSV in Git to preserve annotation provenance.
- Keep one row per file to ensure deterministic file-to-image annotation mapping.
