from odoo import models, fields, api


class AccountMove(models.Model):
    """ Heredamos todos los metodos que de alguna manera llamen a tax.compute_all y les pasamos la fecha"""
    _inherit = "account.move"

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        res = super()._compute_amount()
        for move in self.filtered(lambda x: x.state == 'draft'):
            tax_ids = move.mapped('invoice_line_ids').mapped('tax_ids').filtered(lambda x: x.minimum_perception_amount > 0.0)
            for tax in tax_ids:
                tax_amount = 0.0
                for line in move.mapped('invoice_line_ids').filtered(lambda l: tax in l.tax_ids):
                    tax_amount += tax.with_context(force_price_include=False, calculate_perception=True)._compute_amount(
                        line.price_subtotal, line.price_subtotal, 1.0, line.product_id, line.partner_id)
                if tax_amount >= tax.minimum_perception_amount:
                    if move.move_type != 'out_refund':
                        move.with_context(calculate_perception=True).update_partner_tax_iibb_invoice()
        return res

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
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                context = dict(tax.env.context)
                context.update({'calculate_perception': self._context.get('calculate_perception', False)})
                tax.env.context = context
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
        if not taxes:
            taxes = self.tax_ids.with_context(calculate_perception=self._context.get('calculate_perception', False))
        return super(AccountMoveLine, self)._get_price_total_and_subtotal(
            price_unit=price_unit, quantity=quantity, discount=discount, currency=currency,
            product=product, partner=partner, taxes=taxes, move_type=move_type)

    def _get_fields_onchange_balance(
            self, quantity=None, discount=None, amount_currency=None, move_type=None,
            currency=None, taxes=None, price_subtotal=None, force_computation=False):
        invoice = self.move_id.reversed_entry_id or self.move_id
        invoice_date = invoice.invoice_date or fields.Date.context_today(self)
        self = self.with_context(invoice_date=invoice_date)
        return super(AccountMoveLine, self)._get_fields_onchange_balance(quantity=quantity, discount=discount,
                                                                         amount_currency=amount_currency, move_type=move_type,
                                                                         currency=currency, taxes=taxes,
                                                                         price_subtotal=price_subtotal, force_computation=force_computation)

    # TODO faltaria heredar al momento de creacion porque se llama a _get_price_total_and_subtotal_model y no estamos
    # teniendo en cuenta la fecha que podria pasarse en vals_list
    # @api.model_create_multi
    # def create(self, vals_list):
    type_tax_use = fields.Selection(related='tax_line_id.type_tax_use', string='Tax Scope',
                                   readonly=True, store=True)
