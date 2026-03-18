# Changelog

## [17.0.1.5.0] - 2026-03-18

### Added
- `_build_aliquot_dict`: helper that reads a padron file and returns a `{cuit: (nro, aliquot)}` dict, with optional CUIT filtering for efficiency.
- `action_load_padron`: new action that decompresses the padron ZIP, locates Per/Ret files, and bulk-upserts `res.partner.arba_alicuot` records for all partners with a CUIT.

### Improved
- `descompress_file`: replaced temp-file approach with an in-memory `BytesIO` stream, removing the `tempfile` dependency.
- `find_file`: simplified date formatting with `%02d%d`, corrected the regex pattern, and added `re.IGNORECASE` for more robust file matching.

## [17.0.1.4.0]

- Previous release (see git history).
