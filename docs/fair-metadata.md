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

## References

- FAIR principles: https://doi.org/10.1038/sdata.2016.18
- REMBI: https://doi.org/10.1038/s41592-021-01166-8
- MIFA: https://www.nature.com/articles/s41592-025-02663-5
- OME data model: https://doi.org/10.1186/gb-2005-6-5-r47
- OMERO platform: https://doi.org/10.1038/nmeth.1896
- Bio-Formats: https://doi.org/10.1083/jcb.201004104
- OME-TIFF: https://docs.openmicroscopy.org/ome-model/latest/ome-tiff/
