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
