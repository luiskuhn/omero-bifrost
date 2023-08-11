# OMERO-Bifrost

Bifrost bridge for large-scale transfer of bioimage data using an OMERO server. A simplified Python CLI tool and package to transfer image data/metadata from and to an OMERO server.

![omero-bifrost](docs/images/bifrost_img.png)

### Requirements

- Python `3.8`
- typer `0.9.0`
- rich `13.5.2`
- zeroc-ice `3.6.5`
- omero-py `5.15.0`
- omero-upload `0.4.0`


### Install with PyPI

`pip install omero-bifrost`

### Usage

Type `omero-bifrost --help` to see the full range of commands and subcommands.

---

### Development notes

To install packages in `requirements.txt` in the current conda env.:

`pip install -r requirements.txt`

To test package, install using pip:

`pip install -e .`

