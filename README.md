# OMERO-Bifrost

<img align="left" width="100" height="100" src="https://github.com/qbicsoftware/omero-bifrost/blob/main/docs/images/bifrost_img.png?raw=true">

**OMERO-Bifrost** is a workflow-oriented abstraction layer for interoperable image and (meta)data access across a constellation of [OMERO servers](https://omero.readthedocs.io/en/stable/).

It exposes consistent read/write operations through a Python package and CLI so the same data-management logic can run in local, HPC, and cloud environments. The primary design target is integration with Nextflow and nf-core processes/modules, where deterministic command interfaces and explicit file artifacts are key for portability and reproducibility.

OMERO-Bifrost is FAIR-oriented by design and aligns metadata operations with community standards and formats, including REMBI and MIFA reporting expectations, the OME data model, Bio-Formats interoperability, and OME-TIFF exchange.

<br>

---

### Requirements

- Python `3.8`
- typer `0.9.0`
- rich `13.5.2`
- zeroc-ice `3.6.5`
- omero-py `5.13.1` (downgraded from `5.15.0` given ezomero `2.1.0` requirements)
- omero-upload `0.4.0`
- ezomero `2.1.0`

### Install with PyPI

`pip install omero-bifrost`

### Usage

Type `omero-bifrost --help` to see the full range of commands and subcommands.

Current command groups:
- `query`: inspect OMERO objects and metadata-filtered image IDs
- `push`: import images and write annotations to OMERO
- `pull`: export OME-TIFFs and download original files

---

### Configuration

`omero-bifrost` reads credentials from a properties file (default: `./imaging_config.properties`).

Minimal single-server format:

```ini
[OmeroServerSection]
omero.username = my_user
omero.password = my_password
omero.host = omero.example.org
omero.port = 4064
# Optional group context (group name or numeric id)
omero.group = my-lab-group
```

Multi-server format (recommended for constellation-style deployments):

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

Notes:
- `omero.group` is optional for backward compatibility.
- When provided, it is propagated to both BlitzGateway connections and CLI-backed commands.
- The current built-in parser consumes `OmeroServerSection` directly; profile-specific sections are typically selected in workflow wrappers that materialize the active profile as `OmeroServerSection` at runtime.

#### Profile-oriented usage examples

In pipeline wrappers (e.g., Nextflow module entrypoints), a `--server-profile` flag is commonly used to pick `eu`, `us`, or `archive` before invoking `omero-bifrost`.

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

### Nextflow / nf-core orientation

The CLI is designed for process-level composition, where each invocation performs one focused operation with explicit, testable inputs and outputs.

For pipeline design:
- Keep OMERO credentials and group context in mounted config files or secret-managed environment material.
- Prefer commands that emit files (`--output` for query commands, exported data for pull commands).
- Pass image IDs and selection state between processes via TSV artifacts.
- Keep process logic server-agnostic by externalizing endpoint-specific settings to config files.

---

### FAIR metadata and standards alignment

OMERO-Bifrost supports FAIR-oriented workflows by combining stable operational interfaces with established microscopy standards:

- **REMBI / MIFA guidance**: structure metadata capture and annotation so datasets remain understandable and reusable across projects.
- **OME data model**: use OME semantics as a canonical conceptual backbone for microscopy metadata.
- **Bio-Formats interoperability**: support ingestion/export pathways compatible with broadly used microscopy formats.
- **OME-TIFF exchange**: provide a portable representation for downstream analysis, sharing, and archival use cases.

Operationally, this means query/push/pull workflows should preserve provenance-relevant fields and generate machine-readable intermediate artifacts for reproducible downstream processing.

---

### Documentation

- [Architecture and constellation model](docs/architecture.md)
- [Nextflow / nf-core integration guide](docs/nextflow-nfcore.md)
- [FAIR metadata and standards mapping](docs/fair-metadata.md)

---

### Scientific references

- **FAIR principles**: Wilkinson MD *et al.* “The FAIR Guiding Principles for scientific data management and stewardship.” *Scientific Data* (2016). https://doi.org/10.1038/sdata.2016.18
- **REMBI**: Sarkans U *et al.* “REMBI: Recommended Metadata for Biological Images.” *Nature Methods* (2021). https://doi.org/10.1038/s41592-021-01166-8
- **MIFA**: MIFA consortium paper (community framework for microscopy metadata in AI and machine-actionable workflows). *Nature Methods* (2025). https://www.nature.com/articles/s41592-025-02663-5
- **OME data model**: Goldberg IG *et al.* “The Open Microscopy Environment (OME) Data Model and XML File: open tools for informatics and quantitative analysis in biological imaging.” *Genome Biology* (2005). https://doi.org/10.1186/gb-2005-6-5-r47
- **OMERO platform**: Allan C *et al.* “OMERO: flexible, model-driven data management for experimental biology.” *Nature Methods* (2012). https://doi.org/10.1038/nmeth.1896
- **Bio-Formats**: Linkert M *et al.* “Metadata matters: access to image data in the real world.” *Journal of Cell Biology* (2010). https://doi.org/10.1083/jcb.201004104
- **OME-TIFF**: OME Consortium specification page. https://docs.openmicroscopy.org/ome-model/latest/ome-tiff/

### Tooling and API documentation

- **omero-py** (Python bindings): https://omero.readthedocs.io/en/stable/developers/Python.html
- **OMERO CLI documentation**: https://omero.readthedocs.io/en/stable/users/cli/index.html
- **OMERO API documentation (developer index)**: https://omero.readthedocs.io/en/stable/developers/
- **ezomero** (high-level OMERO Python helpers): https://thejacksonlaboratory.github.io/ezomero/
- **Bio-Formats developer/user docs**: https://bio-formats.readthedocs.io/

---

### Development notes

To install packages in `requirements.txt` in the current conda env.:

`pip install -r requirements.txt`

To test package, install using pip:

`pip install -e .`
