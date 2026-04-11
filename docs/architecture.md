# Architecture: OMERO-Bifrost as an abstraction layer

## Purpose

OMERO-Bifrost provides a stable automation layer over one or more OMERO servers, enabling pipelines to execute the same read/write data operations independent of where the underlying server is hosted.

In this context, a **constellation** means multiple OMERO endpoints coordinated through one workflow-facing command interface.

## Core design principle

The tool separates:

- **Workflow concerns**: deterministic commands, file-based artifacts, process chaining.
- **Infrastructure concerns**: server host, credentials, group context, and endpoint-specific access.

This separation allows Nextflow/nf-core modules to remain portable while endpoint details are supplied by configuration.

## Abstraction boundary

OMERO-Bifrost intentionally exposes a compact set of operational capabilities:

- **query**: discover/filter objects and emit image identifiers.
- **push**: import image data and write metadata/annotations.
- **pull**: export OME-TIFF and/or retrieve original files.

These operations are intended to be composable building blocks for workflows rather than a full replacement for interactive OMERO clients.

## Reproducibility implications

By favoring explicit inputs and outputs per command, pipelines can:

- materialize intermediate state as artifacts (e.g., TSV of image IDs),
- rerun individual process steps deterministically,
- improve auditability and provenance tracking.

## Metadata and FAIR intent

OMERO-Bifrost is FAIR-oriented and designed to integrate with community standards such as REMBI, MIFA, the OME model, and exchange formats like OME-TIFF (with Bio-Formats-compatible pathways where applicable).
