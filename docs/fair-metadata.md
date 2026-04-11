# FAIR metadata and standards mapping

## Scope

This document summarizes how OMERO-Bifrost is intended to support FAIR-oriented metadata handling in workflow automation contexts.

## Standards and formats in scope

### REMBI

REMBI provides recommendations for minimum information reporting in bioimaging. In OMERO-Bifrost workflows, REMBI-aligned fields should be captured and propagated as structured metadata where possible.

### MIFA

MIFA offers guidance for microscopy experiment annotation and quality-related metadata. OMERO-Bifrost metadata operations should preserve these annotations to improve interpretability and reuse.

### OME data model

The OME model acts as a canonical semantic framework for microscopy metadata. OMERO-Bifrost operations should maintain consistency with OME entities/relationships during query, ingestion, annotation, and export workflows.

### Bio-Formats

Bio-Formats interoperability supports broad microscopy format compatibility. OMERO-Bifrost workflows should prefer ingestion/export paths that remain compatible with Bio-Formats-enabled tooling in downstream analysis ecosystems.

### OME-TIFF

OME-TIFF provides a portable, metadata-aware exchange format for microscopy data. In OMERO-Bifrost, OME-TIFF export serves reproducible transport between acquisition, management, and analysis stages.

## Practical FAIR implementation notes

To improve findability, accessibility, interoperability, and reusability in pipelines:

- preserve provenance-relevant metadata during push/pull operations,
- keep machine-readable intermediate artifacts for selection and transformation steps,
- standardize metadata field naming in workflow outputs,
- document assumptions and transformations in pipeline/module docs.

## Implementation principle

OMERO-Bifrost does not replace domain standards; it operationalizes them by providing stable workflow-facing commands that can be embedded in reproducible process graphs.
