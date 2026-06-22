# Changelog

All notable changes to this module will be documented in this file.

## [17.0.1.15.0] - 2026-06-19

### Fixed
- `account.payment.action_post`: the `rec.l10n_ar_withholding_line_ids = commands`
  write that assigns sequence numbers to withholding lines was incorrectly placed
  **inside** the `for line in rec.l10n_ar_withholding_line_ids` loop. This caused
  one full `_synchronize_to_moves` cycle (delete + rebuild of all withholding move
  lines) per withholding line instead of once at the end. With N withholding lines,
  N−1 redundant sync cycles ran before posting, each temporarily unbalancing the
  OP-X move and rebuilding it. The write is now placed **after** the loop so the
  sequence numbers for all lines are committed in a single operation, reducing
  unnecessary sync cycles and the risk of intermediate unbalanced states.

## [17.0.1.14.1] - 2026-05-22

### Fixed
- `account.move.line._compute_withholding`: corrected the `withholding_id`
  association on a move line when the payment has multiple withholdings with
  the same `tax_id`. The previous filter
  `payment_id.l10n_ar_withholding_line_ids.filtered(lambda x: x.tax_id == rec.tax_line_id)`
  could return a multi-record recordset; assigning it to a Many2one silently
  kept only the first record, so every move line for that tax ended up
  pointing to the same `l10n_ar.payment.withholding` (same certificate
  number, same base, etc.). Now, when more than one match is found, we
  disambiguate by `name` (the move line's `name` matches the withholding's
  `name` because the move sync sets it that way), and always assign `[:1]`
  to the Many2one to avoid the silent bug. This fixes consumers of
  `line.withholding_id` in `l10n_ar_account_tax_settlement` (SIFERE,
  DGR Mendoza, AGIP, DREI, SIRCAR, Misiones, etc.).

## [17.0.1.14.0]

### Fixed
- `account.payment._prepare_move_line_default_vals`: the loop that adjusts the
  counterpart line by `wth_amount` now iterates only over the lines returned by
  `super()` (which expose `debit`/`credit`). The withholding write-off lines
  (which only expose `balance`) are concatenated to the result afterwards, so a
  misconfigured withholding account no longer raises `KeyError: 'debit'` and
  the intent of the original code is preserved.

### Added
- `account.payment._check_withholding_accounts_types`: new early validation
  that runs at the start of `_prepare_move_line_default_vals`. It raises a
  `UserError` with an actionable message when any account used for a
  withholding line, or the company's `l10n_ar_tax_base_account_id`, is
  configured with `account_type` `liability_payable` or `asset_receivable`.
  Previously this misconfiguration surfaced as Odoo's native
  *"must include one and only one receivable/payable account"* error, which is
  cryptic for end users; now the error points to the exact account and the tax
  using it.
