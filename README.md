# OMERO-Bifrost

<img align="left" width="100" height="100" src="https://github.com/qbicsoftware/omero-bifrost/blob/main/docs/images/bifrost_img.png?raw=true">

Bifrost bridge for large-scale transfer of bioimage data using [OMERO servers](https://omero.readthedocs.io/en/stable/). `omero-bifrost` provides a Python package and CLI designed for workflow automation, especially in Nextflow and nf-core pipelines.

The tool focuses on reproducible access to image data and FAIR-oriented metadata operations while evolving toward a constellation model: multiple OMERO endpoints coordinated through one automation layer.

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

The CLI is intended to be called from workflow process scripts where each command performs one focused data operation (query, import, annotate, export) with explicit file inputs/outputs.

For pipeline design:
- Keep OMERO credentials and group context in mounted config files or secret-managed env material.
- Prefer command invocations that emit files (`--output` for query commands, exported data for pull commands).
- Use image ID TSV artifacts to pass selected records between processes.

---

### Development notes

To install packages in `requirements.txt` in the current conda env.:

`pip install -r requirements.txt`

To test package, install using pip:

`pip install -e .`
