# Changelog

## [17.0.1.6.3] - 2026-07-15

### Fixed

- `_compute_partner_credit_warning`: se corrige `KeyError: 'amount_total_company_currency'`
  al crear una factura. El core (`account_move.py`) lee `move.currency_id` para decidir
  si necesita la clave `amount_total` o `amount_total_company_currency` de
  `move.tax_totals`, y accede a `move.tax_totals` recién después. En una factura nueva
  sin diario asignado, `currency_id` todavía está vacío en ese primer momento, así que
  el core decide que necesita `amount_total_company_currency`; pero al acceder a
  `tax_totals` se dispara nuestro `_compute_tax_totals` (ver fix 17.0.1.6.2), que rellena
  ese mismo `currency_id` vacío con la moneda de la compañía como efecto colateral,
  dejando el diccionario armado como si la moneda coincidiera con la de la compañía (sin
  esa clave). Se fuerza el cálculo de `tax_totals` (estabilizando ese fallback) antes de
  delegar en `super()`, y se garantiza que la clave siempre esté presente.

## [17.0.1.6.2] - 2026-07-13

### Fixed

- `_compute_tax_totals`: se corrige `ValueError: Expected singleton: res.currency()`
  al crear una factura/asiento. El core de Odoo (`account_move.py`, desde el fix de
  negative zeroes en las totales del PDF) llama `move.currency_id.is_zero(...)` sin el
  fallback a `journal_id.currency_id`/`company_id.currency_id` que usa el resto del
  método, y `currency_id` puede llegar vacío en medio de la cadena de onchanges (p. ej.
  antes de que se fije el diario). Se rellena `invoice.currency_id` con ese mismo
  fallback antes de delegar en `super()` para evitar el crash.

## [17.0.1.6.1] - 2026-06-11

### Fixed

- Se corrige error al calcular retenciones en empresas que son agentes de
  retención de AGIP pero no de ARBA. Cuando el impuesto tiene la jurisdicción
  ARBA (902) pero la empresa no tiene clave CIT configurada, en lugar de un
  diálogo bloqueante se muestra una notificación no bloqueante (toast) indicando
  que se omitió la consulta al padrón ARBA.

## [17.0.1.6.0] - 2026-05-04

### Fixed
- `_l10n_ar_get_invoice_totals_for_report`: corrected `tax_group_amount_company_currency` for foreign-currency invoices. `_prepare_tax_totals` recomputes taxes from base lines using an already-rounded rate (`amount_currency / balance`), introducing rounding drift vs. the balances stored in the journal entry. For foreign-currency invoices the fix replaces those recomputed values with the real posted balances from the `tax` display-type lines.

## [17.0.1.5.0] - 2026-03-18

### Added
- `_build_aliquot_dict`: helper that reads a padron file and returns a `{cuit: (nro, aliquot)}` dict, with optional CUIT filtering for efficiency.
- `action_load_padron`: new action that decompresses the padron ZIP, locates Per/Ret files, and bulk-upserts `res.partner.arba_alicuot` records for all partners with a CUIT.

### Improved
- `descompress_file`: replaced temp-file approach with an in-memory `BytesIO` stream, removing the `tempfile` dependency.
- `find_file`: simplified date formatting with `%02d%d`, corrected the regex pattern, and added `re.IGNORECASE` for more robust file matching.

## [17.0.1.4.0]

- Previous release (see git history).
