# Changelog

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
