from odoo import models


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

    def _compute_tax_totals(self):
        """ Mandamos en contexto el invoice_date para cauclo de impuesto con partner aliquot"""
        invoices = self.filtered(lambda x: x.is_invoice(include_receipts=True))
        for invoice in invoices:
            invoice = invoice.with_context(invoice_date=invoice.invoice_date if not invoice.reversed_entry_id else invoice.reversed_entry_id.invoice_date)
            super(AccountMove, invoice)._compute_tax_totals()
        super(AccountMove, self - invoices)._compute_tax_totals()

    def _l10n_ar_get_invoice_totals_for_report(self):
        """ Mandamos en contexto el invoice_date para cauclo de impuesto con partner aliquot
        cuando imprimos el reporte de factura """
        self.ensure_one()
        tax_totals = super(AccountMove, self.with_context(invoice_date=self.invoice_date))._l10n_ar_get_invoice_totals_for_report()

        # _prepare_tax_totals computes tax_group_amount_company_currency by recomputing taxes
        # from base lines using rate = amount_currency / balance (already rounded), which
        # introduces rounding drift vs. the balance actually stored in the journal entry.
        # For foreign-currency invoices we replace those values with the real posted balances.
        if self.currency_id != self.company_id.currency_id:
            sign = -1 if self.is_inbound(include_receipts=True) else 1
            tax_group_balance = {}
            for line in self.line_ids.filtered(lambda l: l.display_type == 'tax'):
                group_id = line.tax_line_id.tax_group_id.id
                tax_group_balance[group_id] = tax_group_balance.get(group_id, 0.0) + sign * line.balance

            for subtotal_groups in tax_totals.get('groups_by_subtotal', {}).values():
                for group in subtotal_groups:
                    group_id = group.get('tax_group_id')
                    if group_id in tax_group_balance:
                        group['tax_group_amount_company_currency'] = tax_group_balance[group_id]

        return tax_totals
