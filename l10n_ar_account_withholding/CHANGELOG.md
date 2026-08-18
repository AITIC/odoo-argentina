# Changelog

## [15.0.1.4.2] - 2026-08-18

### Fixed

- `_recompute_tax_lines`: el resguardo de 15.0.1.4.1 solo completaba `move.currency_id`, pero el
  `ValueError: Expected singleton: res.currency()` seguía ocurriendo porque, en el core
  (`account_move.py`), `_get_tax_grouping_key_from_base_line` arma la clave de agrupación de
  impuestos usando `base_line.currency_id.id` (la moneda de la **línea**, no la del `move`). El
  campo `currency_id` de `account.move.line` no tiene `default`, así que si una línea (típicamente
  la de anticipo) se arma como registro en memoria sin `currency_id`, el core hace
  `self.env['res.currency'].browse(False)` y luego `currency.is_zero(...)` explota con
  `ensure_one()` sobre un recordset vacío. Ahora, antes de delegar en `super()`, además de
  `move.currency_id` también se completa el `currency_id` de cualquier línea (`move.line_ids`) que
  llegue vacía, usando la moneda de la compañía como resguardo, con un `_logger.warning` en ambos
  casos (con id/nombre del move y cantidad de líneas afectadas) para poder rastrear qué orden o
  factura llegó sin moneda resuelta.

## [15.0.1.4.1] - 2026-08-14

### Fixed

- `_recompute_tax_lines`: se agrega un resguardo ante `ValueError: Expected singleton: res.currency()`
  al crear una factura de anticipo (`sale.advance.payment.inv`). El core (`account_move.py`) arma un
  `taxes_map` usando `move.currency_id` para decidir si un importe de impuesto es cero
  (`currency.is_zero(...)`); si el `move` en memoria llega a este punto sin `currency_id` resuelto,
  ese `currency` termina siendo un recordset vacío y `ensure_one()` explota. Antes de delegar en
  `super()`, se completa `currency_id` con la moneda de la compañía como resguardo y se deja un
  `_logger.warning` con el id/nombre del move afectado, para poder rastrear después qué orden o
  factura llegó sin moneda resuelta.