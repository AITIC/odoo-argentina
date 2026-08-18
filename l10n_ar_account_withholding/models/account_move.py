import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """ Heredamos todos los metodos que de alguna manera llamen a tax.compute_all y les pasamos la fecha"""
    _inherit = "account.move"

    def _get_tax_factor(self):
        tax_factor = super()._get_tax_factor()
        doc_letter = self.l10n_latam_document_type_id.l10n_ar_letter
        # if we receive B invoices, then we take out 21 of vat
        # this use of case if when company is except on vat for eg.
        if tax_factor == 1.0 and doc_letter == 'B':
            tax_factor = 1.0 / 1.21
        return tax_factor

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
        """
        Hacemos esto para disponer de fecha de factura y cia para calcular
        impuesto con código python (por ej. para ARBA).
        Aparentemente no se puede cambiar el contexto a cosas que se llaman
        desde un onchange (ver https://github.com/odoo/odoo/issues/7472)
        entonces usamos este artilugio
        """
        invoice = self.reversed_entry_id or self
        invoice_date = invoice.invoice_date or fields.Date.context_today(self)
        self = self.with_context(invoice_date=invoice_date)
        for move in self:
            fallback_currency = move.currency_id or move.company_id.currency_id or self.env.company.currency_id
            if not move.currency_id:
                _logger.warning(
                    "account.move id=%s (%s) sin currency_id al recalcular impuestos; "
                    "se usa la moneda de la compañía (%s) como resguardo.",
                    move.id or 'new', move.name or move.ref or '/', fallback_currency.name,
                )
                move.currency_id = fallback_currency
            # account.move.line.currency_id no tiene default: si una línea (ej. la de
            # anticipo) se arma sin currency_id, _get_tax_grouping_key_from_base_line del
            # core usa base_line.currency_id.id (False) y currency.is_zero() explota con
            # "Expected singleton: res.currency()".
            lines_without_currency = move.line_ids.filtered(lambda l: not l.currency_id)
            if lines_without_currency:
                _logger.warning(
                    "account.move id=%s (%s): %s línea/s sin currency_id al recalcular "
                    "impuestos; se completan con %s como resguardo.",
                    move.id or 'new', move.name or move.ref or '/',
                    len(lines_without_currency), fallback_currency.name,
                )
                lines_without_currency.currency_id = fallback_currency
        return super(AccountMove, self)._recompute_tax_lines(recompute_tax_base_amount=recompute_tax_base_amount, tax_rep_lines_to_recompute=tax_rep_lines_to_recompute)

    @api.onchange('invoice_date', 'reversed_entry_id')
    def _onchange_tax_date(self):
        """ Si cambia la fecha o cambiamos el refund asociado tenemos que recalcular los impuestos """
        self._onchange_invoice_date()
        if self.invoice_line_ids.mapped('tax_ids').filtered(lambda x: x.amount_type == 'partner_tax'):
            # si no recomputamos no se guarda el cambio en las lineas
            self.line_ids._onchange_price_subtotal()
            self._recompute_dynamic_lines(recompute_all_taxes=True)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_price_total_and_subtotal(
            self, price_unit=None, quantity=None, discount=None, currency=None,
            product=None, partner=None, taxes=None, move_type=None):
        invoice = self.move_id.reversed_entry_id or self.move_id
        invoice_date = invoice.invoice_date or fields.Date.context_today(self)
        self = self.with_context(invoice_date=invoice_date)
        return super(AccountMoveLine, self)._get_price_total_and_subtotal(
            price_unit=price_unit, quantity=quantity, discount=discount, currency=currency,
            product=product, partner=partner, taxes=taxes, move_type=move_type)

    def _get_fields_onchange_balance(
            self, quantity=None, discount=None, amount_currency=None, move_type=None,
            currency=None, taxes=None, price_subtotal=None, force_computation=False):
        invoice = self.move_id.reversed_entry_id or self.move_id
        invoice_date = invoice.invoice_date or fields.Date.context_today(self)
        self = self.with_context(invoice_date=invoice_date)
        return super(AccountMoveLine, self)._get_fields_onchange_balance(
            quantity=quantity, discount=discount, amount_currency=amount_currency, move_type=move_type,
            currency=currency, taxes=taxes, price_subtotal=price_subtotal, force_computation=force_computation)

    # TODO faltaria heredar al momento de creacion porque se llama a _get_price_total_and_subtotal_model y no estamos
    # teniendo en cuenta la fecha que podria pasarse en vals_list
    # @api.model_create_multi
    # def create(self, vals_list):
