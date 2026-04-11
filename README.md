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

`omero-bifrost` reads credentials from a properties file (default: `./imaging_config.properties`):

```ini
[OmeroServerSection]
omero.username = my_user
omero.password = my_password
omero.host = omero.example.org
omero.port = 4064
# Optional group context (group name or numeric id)
omero.group = my-lab-group
```

Notes:
- `omero.group` is optional for backward compatibility.
- When provided, it is propagated to both BlitzGateway connections and CLI-backed commands.

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

### Development notes

To install packages in `requirements.txt` in the current conda env.:

`pip install -r requirements.txt`

To test package, install using pip:

`pip install -e .`
