# Changelog

All notable changes to this module will be documented in this file.

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
