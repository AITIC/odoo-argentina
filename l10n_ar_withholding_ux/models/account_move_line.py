##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
# import odoo.addons.decimal_precision as dp
# from odoo.exceptions import ValidationError
# from dateutil.relativedelta import relativedelta
# import datetime


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    withholding_id = fields.Many2one('l10n_ar.payment.withholding', compute='_compute_withholding')

    def _compute_withholding(self):
        for rec in self:
            if rec.tax_line_id and rec.payment_id:
                withholdings = rec.payment_id.l10n_ar_withholding_line_ids.filtered(
                    lambda x: x.tax_id == rec.tax_line_id)
                # Cuando hay varias retenciones del mismo impuesto en un mismo
                # pago, desambiguamos por el name del apunte (que se setea con
                # el name del withholding al sincronizar el move). Sin esto,
                # asignar un recordset multiple a un Many2one se queda con el
                # primero y todas las lineas terminan apuntando al mismo
                # certificado.
                if len(withholdings) > 1 and rec.name:
                    by_name = withholdings.filtered(lambda x: x.name == rec.name)
                    if by_name:
                        withholdings = by_name
                rec.withholding_id = withholdings[:1]
            else:
                rec.withholding_id = False
