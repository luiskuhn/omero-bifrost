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

## OMERO CLI execution and error contract

Subprocess-backed OMERO operations are centralized in `omero_cli_runner.run_omero_cli`, which always executes argument lists (`shell=False`) and captures `stdout`/`stderr` as text for deterministic downstream handling.

Contract details:

- Successful calls return a typed `CommandResult` with `returncode`, `stdout`, `stderr`, `cmd`, and optional `artifacts`.
- Non-zero OMERO CLI exits raise `OmeroCliCommandError` and include the captured `CommandResult`.
- Missing or malformed expected records in stdout (e.g., `Image:`, `OriginalFile:`, `TagAnnotation:`, `FileAnnotation:`, `ImageAnnotationLink:`) raise `OmeroCliParseError`.
- CLI handlers map these controlled exceptions to deterministic terminal output using `ERROR|<ExceptionType>|<message>` and exit with non-zero status.

This behavior is intended for workflow engines (Nextflow/nf-core) so failures are explicit, parseable, and never represented as ambiguous empty strings/lists.
