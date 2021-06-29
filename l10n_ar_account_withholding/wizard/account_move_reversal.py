from odoo import models, fields


class AccountMoveReversal(models.TransientModel):

    _inherit = "account.move.reversal"

    def reverse_moves(self):
        """ Forzamos fecha de la factura original para que el amount total de la linea se calcule bien"""
        invoice_date = self.move_ids and self.move_ids[0].date or fields.Date.context_today
        self = self.with_context(invoice_date=invoice_date)
        return super(AccountMoveReversal, self).reverse_moves()
